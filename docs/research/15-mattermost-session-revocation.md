# Mattermost session revocation and expiry as seen by a WebSocket client

Status: complete (2026-09-03). Resolves GitHub issue #50. Sources are `master` of github.com/mattermost/mattermost (fetched 2026-09-03) unless noted; code is quoted verbatim. "unverified" marks anything not confirmed from a primary source. Builds on `01-mattermost-websocket-protocol.md` (§3 heartbeat constants, §7 "session expiry is silent").

## 0. Answer in three sentences

The server **never closes** an open WebSocket because its session was revoked or expired: revocation clears the connection's cached session (`InvalidateCache()`), the next `IsBasicAuthenticated()` re-reads the session from cache/DB, and on failure the connection is left open with an empty token — `ShouldSendEvent` returns `false` for every event and every JSON request is answered with `status: FAIL`, `error.id = api.web_socket_router.not_authenticated.app_error` (401). For a **bot token (personal access token)** most "session" operations are harmless, because `GetSession` transparently **recreates a session from the token row** as long as the token is active and the user is not deactivated; only PAT delete/disable, bot disable/user deactivation, or `EnableUserAccessTokens=false` (non-bot) make the connection go permanently silent. The fastest reliable client-side detector is therefore the **JSON `ping`** (it requires auth) — the error reply arrives within one ping period — backed by a REST probe whose `401` body `id` distinguishes the cause.

## 1. `web_conn.go`: the connection's own view of its session

Source: https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_conn.go

Each `WebConn` caches three things atomically: `session` (`atomic.Pointer`), `sessionToken` and `sessionExpiresAt`. They are seeded in `NewWebConn` (`wc.SetSessionExpiresAt(cfg.Session.ExpiresAt)`). There is no separate `webConnSessionCache` type; the "web conn session cache" in function names refers to these three fields.

```go
func (wc *WebConn) IsAuthenticated() bool {
	return wc.IsBasicAuthenticated() && wc.IsMFAAuthenticated()
}

func (wc *WebConn) IsBasicAuthenticated() bool {
	if wc.GetSessionExpiresAt() < model.GetMillis() {
		if wc.GetSessionToken() == "" {
			return false
		}
		session, err := wc.Suite.GetSession(wc.GetSessionToken())
		if err != nil {
			if err.StatusCode >= http.StatusBadRequest && err.StatusCode < http.StatusInternalServerError {
				wc.Platform.logger.Debug("Invalid session.", mlog.Err(err))
			} else {
				wc.Platform.logger.Error("Could not get session", mlog.String("session_token", wc.GetSessionToken()), mlog.Err(err))
			}
			wc.SetSessionToken("")
			wc.SetSession(nil)
			wc.SetSessionExpiresAt(0)
			return false
		}
		wc.SetSession(session)
		wc.SetSessionExpiresAt(session.ExpiresAt)
	}
	return true
}
```

Consequences:

- The re-read happens **only when `sessionExpiresAt < now`**. Nothing in the file polls the store on a timer. For a PAT-backed session `ExpiresAt` is ~100 years ahead (§3), so without an external `InvalidateCache()` the connection would never notice anything.
- On a failed re-read the token is **wiped** (`SetSessionToken("")`), so every later `IsBasicAuthenticated()` returns `false` immediately and permanently. The connection is not closed — the only statement touching the socket after an auth failure is the `return false`. Confirmed by asking for every `Close`/`CloseMessage` site: none is reached because of session state.
- Note the `Error`-level log includes `session_token` on 5xx store errors (server-side log hygiene issue, not ours).

`InvalidateCache()` is the hook the hub uses after revocation:

```go
func (wc *WebConn) InvalidateCache() {
	wc.allChannelMembers = nil
	wc.lastAllChannelMembersTime = 0
	wc.SetSession(nil)
	wc.SetSessionExpiresAt(0)
}
```

Setting `sessionExpiresAt = 0` forces the next `IsBasicAuthenticated()` to call `Suite.GetSession(token)`, which is `App.GetSession` (§3) — cache → DB → PAT fallback.

`ShouldSendEvent` starts with the auth check, so a de-authenticated connection receives **no events at all**, not even `hello`:

```go
func (wc *WebConn) ShouldSendEvent(msg *model.WebSocketEvent) bool {
	if !wc.IsAuthenticated() {
		return false
	}
	...
```

`IsMFAAuthenticated()` builds a request context from the cached session and calls `Suite.MFARequired(c, http.MethodGet)`. With a nil session that returns `api.context.get_session.app_error` (401), but it is short-circuited by `IsBasicAuthenticated()` being false first. `MFARequired` returns `nil` for `user.IsBot` and for `session.IsOAuth`, so MFA enforcement can never de-authenticate a bot socket (https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/authentication.go).

The **auth ticker** is only a start-up guard:

```go
authCheckInterval = 5 * time.Second
...
case <-authTicker.C:
	if wc.GetSessionToken() == "" {
		wc.Platform.logger.Debug("websocket.authTicker: did not authenticate", mlog.Stringer("ip_address", wc.WebSocket.RemoteAddr()))
		return
	}
	authTicker.Stop()
```

It fires once, 5 s after `writePump` starts; if the client has not authenticated the pump returns (socket closed); otherwise the ticker is stopped forever. There is no later re-check ("no later auth close" — confirmed). Binary frames from an unauthenticated connection end `readPump` (`"binary frames require authentication"`, test `TestWebConnRejectBinaryFrameUnauthenticated` in `web_conn_test.go`); text frames are simply routed to the router, which answers with an error (§4). `web_conn_test.go` has **no** test for expiry/invalidation behaviour.

## 2. `web_hub.go`: what invalidation does to a live connection

Source: https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_hub.go and https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/cluster_handlers.go

```go
func (ps *PlatformService) invalidateWebConnSessionCacheForUserSkipClusterSend(userID string) {
	hub := ps.GetHubForUserId(userID)
	if hub != nil {
		hub.InvalidateUser(userID)
	}
}

func (ps *PlatformService) invalidateWebConnSessionCacheForUser(userID string) {
	ps.invalidateWebConnSessionCacheForUserSkipClusterSend(userID)
	if ps.clusterIFace != nil {
		msg := &model.ClusterMessage{
			Event:    model.ClusterEventInvalidateWebConnCacheForUser,
			SendType: model.ClusterSendBestEffort,
			Data:     []byte(userID),
		}
		ps.clusterIFace.SendClusterMessage(msg)
	}
}
```

Hub loop:

```go
case userID := <-h.invalidateUser:
	for webConn := range connIndex.ForUser(userID) {
		webConn.InvalidateCache()
	}
	if !*h.platform.Config().ServiceSettings.EnableWebHubChannelIteration {
		continue
	}
	err := connIndex.InvalidateCMCacheForUser(userID)
	if err != nil {
		h.platform.Log().Error("Error while invalidating channel member cache", mlog.String("user_id", userID), mlog.Err(err))
		for webConn := range connIndex.ForUser(userID) {
			closeAndRemoveConn(connIndex, webConn)
		}
	}
```

So invalidation **does not drop the connection and does not itself re-read the session**; it only resets the per-connection cache so the *next* `IsAuthenticated()` (next broadcast or next inbound request) re-reads it. The single path that closes sockets here is a DB error in `InvalidateCMCacheForUser` when `EnableWebHubChannelIteration=true` (default `false`) — `closeAndRemoveConn` closes `conn.send`, which makes `writePump` write a `websocket.CloseMessage` and return. `invalidateAll` (used by `ClearSessionCacheForAllUsersSkipClusterSend`, i.e. "revoke sessions of all users" / cache purge) additionally does `webConn.SetSessionToken("")`, which de-authenticates *every* connection for good without closing it.

`HubUnregister` is unrelated to auth: it is called when the pumps end, marks the `WebConn` inactive, and (if all of the user's connections are inactive) schedules the offline-status update. The reaper then deletes it after `inactiveConnReaperInterval = 5m` (see doc 01 §2).

`TestHubSessionRevokeRace` in `web_hub_test.go` documents the intended interplay: register a conn, broadcast a flood, call `wc1.InvalidateCache()` concurrently and assert the hub does not deadlock — i.e. invalidation during broadcast is a supported, non-closing operation (https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_hub_test.go).

## 3. Sessions, revocation, and personal access tokens (`app/session.go`, `platform/session.go`, `model/session.go`)

Sources: https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/session.go, https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/session.go, https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/session.go, https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/config.go

**Revocation chain.** `App.RevokeSession` → `platform.RevokeSession`:

```go
func (ps *PlatformService) RevokeSession(rctx request.CTX, session *model.Session) error {
	if session.IsOAuth {
		if err := ps.RevokeAccessToken(rctx, session.Token); err != nil { return err }
	} else {
		if err := ps.Store.Session().Remove(session.Id); err != nil { ... }
	}
	ps.ClearUserSessionCache(session.UserId)
	ps.invalidateSessionAttributes(session.Id)
	return nil
}

func (ps *PlatformService) ClearUserSessionCache(userID string) {
	ps.ClearSessionCacheForUserSkipClusterSend(userID)
	if ps.clusterIFace != nil {
		msg := &model.ClusterMessage{
			Event:    model.ClusterEventClearSessionCacheForUser,
			SendType: model.ClusterSendReliable,
			Data:     []byte(userID),
		}
		ps.clusterIFace.SendClusterMessage(msg)
	}
}

// cluster_handlers.go
func (ps *PlatformService) ClearSessionCacheForUserSkipClusterSend(userID string) {
	ps.ClearUserSessionCacheLocal(userID)
	ps.invalidateWebConnSessionCacheForUserSkipClusterSend(userID)
}
```

`RevokeAllSessions(userID)` removes each session row then calls `ClearUserSessionCache` once. `RevokeSessionById` looks the session up and calls `RevokeSession`. The app wrappers add only `sendMobileWipeSignal` (a silent push to mobile devices) — **no WebSocket event is published for revocation**. Sessions are also revoked implicitly by `UpdateActive(user, false)` (§6), by `UpdatePassword` when `TerminateSessionsOnPasswordChange` is on (every session except the current one, via `RevokeSessionById`), and by `RevokeSessionsFromAllUsers` (`Store.Session().RemoveAllSessions()` + `ClearAllUsersSessionCache`).

**`GetSession` and the PAT fallback** (app layer, called by `WebConn.IsBasicAuthenticated` via `Suite.GetSession` and by every REST request):

```go
func (a *App) GetSession(token string) (*model.Session, *model.AppError) {
	...
	if session, _ = a.ch.srv.platform.GetSession(rctx, token); session != nil {
		if session.Token != token { return nil, model.NewAppError("GetSession", "api.context.invalid_token.error", ...) }
		if !session.IsExpired() { a.ch.srv.platform.AddSessionToCache(session) }
	}
	if session == nil || session.Id == "" {
		session, appErr = a.createSessionForUserAccessToken(rctx, token)
		if appErr != nil { return nil, model.NewAppError("GetSession", "api.context.invalid_token.error", ...) }
	}
	if session.Id == "" || session.IsExpired() {
		return nil, model.NewAppError("GetSession", "api.context.invalid_token.error", ..., "session is either nil or expired", http.StatusUnauthorized)
	}
	// idle timeout — skipped for user-access-token sessions:
	if *SessionIdleTimeoutInMinutes > 0 && !session.IsOAuth && !session.IsMobileApp() &&
		session.Props[model.SessionPropType] != model.SessionTypeUserAccessToken &&
		!*ExtendSessionLengthWithActivity {
		if (model.GetMillis() - session.LastActivityAt) > timeout {
			return nil, model.NewAppError("GetSession", "api.context.invalid_token.error", ..., "idle timeout", http.StatusUnauthorized)
		}
	}
```

`platform.GetSession` is cache (`sessionCache`, TTL `SessionCacheInMinutes` default 10, size `SessionCacheSize = 35000`) then `Store.Session().Get`. When the row was removed by revocation and the cache was cleared, the **PAT fallback** runs:

```go
token, nErr := a.Srv().Store().UserAccessToken().GetByToken(tokenString)
if !token.IsActive { return nil, NewAppError(..., "app.user_access_token.invalid_or_missing", nil, "inactive_token", 401) }
user, nErr := a.Srv().Store().User().Get(rctx, token.UserId)
if user.DeleteAt != 0 { return nil, NewAppError(..., "app.user_access_token.invalid_or_missing", nil, "inactive_user_id="+user.Id, 401) }
if !*a.Config().ServiceSettings.EnableUserAccessTokens && !user.IsBot { return nil, NewAppError(..., "EnableUserAccessTokens=false", 401) }
session.AddProp(model.SessionPropUserAccessTokenId, token.Id)
session.AddProp(model.SessionPropType, model.SessionTypeUserAccessToken)
if user.IsBot { session.AddProp(model.SessionPropIsBot, model.SessionPropIsBotValue) }
a.ch.srv.platform.SetSessionExpireInHours(session, model.SessionUserAccessTokenExpiryHours)
if token.ExpiresAt > 0 && (session.ExpiresAt == 0 || token.ExpiresAt < session.ExpiresAt) { session.ExpiresAt = token.ExpiresAt }
session, nErr = a.Srv().Store().Session().Save(rctx, session)
a.ch.srv.platform.AddSessionToCache(session)
```

with `SessionUserAccessTokenExpiryHours = 100 * 365 * 24` (`model/session.go`). So **revoking a PAT-backed session is self-healing**: the next `GetSession` re-creates the session unless the token row is gone/disabled or the user is deactivated. This matches the docs: "Personal access tokens do not expire … bypassing the session length limits set in the System Console" and "Once deleted, all sessions using the token are deleted, and any attempts to use the token … are blocked"; on deactivation "the session used by the personal access token is revoked immediately … and a new session won't be created" (https://developers.mattermost.com/integrate/reference/personal-access-token/). `token.ExpiresAt` exists in the model but is `0` for tokens created through the API (`CreateUserAccessToken` only sets `token.Token = model.NewId()` and saves; a session is created lazily at first use, `CreateUserAccessToken` creates none). unverified: whether any UI/API path sets `UserAccessToken.ExpiresAt` on master.

**Token lifecycle functions.** `RevokeUserAccessToken` and `DisableUserAccessToken` first look up the live session (`platform.GetSessionContext(token.Token)`), delete/disable the token row, then `RevokeSession(session)` — so the hub invalidation fires, and the fallback then fails with `inactive_token`/not-found. `EnableUserAccessToken` only flips the row. Bot tokens are ordinary user access tokens: `api4/bot.go` has no token code; tokens for a bot are created via `POST /users/{user_id}/tokens` → `createUserAccessToken`, guarded by `PermissionCreateUserAccessToken` and `SessionHasPermissionToUserOrBot` (https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/api4/user.go). Routes: `POST /users/tokens/revoke|disable|enable`, `POST /users/{user_id}/sessions/revoke`, `POST /users/{user_id}/sessions/revoke/all`, `POST /users/sessions/revoke/all`, `POST /users/logout` (`APIHandler`, no session required), `PUT /users/{user_id}/active`.

**Config field names (verified in `model/config.go`).** `SessionLengthWebInHours`, `SessionLengthMobileInHours`, `SessionLengthSSOInHours` (and their `*InDays` twins, all marked Deprecated in the struct; defaults 30 days on fresh installs, 180 days on upgrade for web/mobile), `SessionCacheInMinutes = 10`, `SessionIdleTimeoutInMinutes = 43200`, `ExtendSessionLengthWithActivity` (`!isUpdate`), `TerminateSessionsOnPasswordChange` (`!isUpdate`), `EnableUserAccessTokens = false`, `EnableWebHubChannelIteration = false`. **There is no `SessionLengthUserAccessTokenInHours`** or any `UserAccessToken`+`SessionLength`/`Expiry` setting — PAT lifetime is the hard-coded 100-year constant. `GetSessionLengthInMillis` returns the *remaining* lifetime for PAT sessions and `ExtendSessionExpiryIfNeeded` (threshold `max(min(1% of length, 1 day), 5 min)` since session start, only when `ExtendSessionLengthWithActivity`) is therefore effectively a no-op for them. `SetSessionExpireInHours` anchors on `CreateAt` unless `ExtendSessionLengthWithActivity` or `CreateAt == 0` (`platform/session.go`).

**Expiry check.** `model.Session.IsExpired()`: `ExpiresAt <= 0 → false; GetMillis() > ExpiresAt → true`. For a login-session token (not a PAT) the WebConn's own `sessionExpiresAt` hits first, `GetSession` returns 401 `api.context.invalid_token.error` ("session is either nil or expired"), and the socket goes silent exactly at `ExpiresAt` (or at the idle timeout, evaluated only on re-read).

## 4. `websocket_router.go`: `not_authenticated` on WS requests

Source: https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/websocket_router.go

Order of checks in `ServeWebSocket`: empty action → `api.web_socket_router.no_action.app_error` (400); `Seq <= 0` → `bad_seq` (400); then the `authentication_challenge` branch; then:

```go
if !conn.IsAuthenticated() {
	err := model.NewAppError("ServeWebSocket", "api.web_socket_router.not_authenticated.app_error", nil, "", http.StatusUnauthorized)
	returnWebSocketError(conn.Platform, conn, r, err)
	return
}
handler, ok := wr.handlers[r.Action]
if !ok { ... "api.web_socket_router.bad_action.app_error" (500) ... }
```

So **every registered action** (`ping`, `get_statuses`, `user_typing`, `presence`, …) returns `not_authenticated` on a de-authenticated connection; `authentication_challenge` is the only exception. `returnWebSocketError` does `err.WipeDetailed()` then `hub.SendMessage(conn, model.NewWebSocketError(r.Seq, err))`. Wire shape (`WebSocketResponse` + `AppError` json tags from `model/utils.go`):

```json
{"status":"FAIL","seq_reply":42,"error":{"id":"api.web_socket_router.not_authenticated.app_error","message":"...","detailed_error":"","status_code":401}}
```

(`request_id` is `omitempty` and empty here; `message` is the i18n text — the en.json entry sits past the fetch truncation, wording unverified.) Note `hub.SendMessage` is a direct write to `conn.send` and does **not** pass through `ShouldSendEvent`, which is why the error reaches a de-authenticated socket while events do not.

The `authentication_challenge` branch is guarded by `if conn.GetSessionToken() != "" { return }` — silently ignored on an authenticated socket. Because a failed re-read wipes the token (§1), the branch becomes reachable again on a de-authenticated socket: a bad token there calls `conn.WebSocket.Close()` (a real close, no error frame), a good one does `SetSession`/`SetSessionToken`/`UserId =` and `HubRegister(conn)` again. Re-registering an already indexed `WebConn` is not an intended flow (the register case calls `connIndex.Add` and sends a second `hello` when `reuseCount == 0`) — unverified whether it is safe; do not rely on in-place re-auth, reconnect instead.

## 5. REST side: `web/handlers.go` and `web/context.go`

Sources: https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/web/handlers.go, https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/web/context.go, https://raw.githubusercontent.com/mattermost/mattermost/master/server/i18n/en.json

```go
if token != "" && tokenLocation != app.TokenLocationCloudHeader && tokenLocation != app.TokenLocationRemoteClusterHeader {
	session, err := c.App.GetSession(token)
	if err != nil {
		c.Logger.Info("Invalid session", mlog.String("error", strings.ReplaceAll(err.Error(), token, tokenDigest(token))))
		if err.StatusCode == http.StatusInternalServerError {
			c.Err = err
		} else if h.RequireSession {
			c.RemoveSessionCookie(w, r)
			c.Err = model.NewAppError("ServeHTTP", "api.context.session_expired.app_error", nil, "token_sha256="+tokenDigest(token), http.StatusUnauthorized)
		}
	} else if !session.IsOAuth && tokenLocation == app.TokenLocationQueryString {
		c.Err = model.NewAppError("ServeHTTP", "api.context.token_provided.app_error", nil, "token_sha256="+tokenDigest(token), http.StatusUnauthorized)
	} else {
		c.AppContext = c.AppContext.WithSession(session)
	}
```

Behaviour:

- Any `GetSession` failure (revoked, expired, idle-timed-out, PAT deleted/disabled, user deactivated) on an `APISessionRequired` route becomes **`401` with `id: "api.context.session_expired.app_error"`** — text "Invalid or expired session, please login again." (en.json). The more specific `api.context.invalid_token.error` / `app.user_access_token.invalid_or_missing` ids from `GetSession` are **not exposed**; they are only logged (with the token replaced by its SHA-256 digest). The body's `detailed_error` is `token_sha256=<hex>`, which is safe to log on our side.
- A store error (5xx) is passed through as-is, so a `500`/`503` on the probe is a dependency failure, not revocation.
- On a route that does not require a session, an invalid token is silently treated as anonymous (no error) — so the liveness probe must hit an `APISessionRequired` route such as `GET /api/v4/users/me`.
- `SessionRequired()` adds two more 401 cases with the same id: `UserAccessToken` (a PAT session while `EnableUserAccessTokens=false` **and** the session is not a bot's) and `UserRequired` (no user id).
- Headers: `X-Request-Id` and `X-Version-Id` are set on every response; for API calls `Content-Type: application/json` and the status code come from `c.Err.StatusCode` with `c.Err.ToJSON()` as the body. `RemoveSessionCookie` writes `Set-Cookie: MMAUTHTOKEN=; Path=<subpath>; Max-Age=0; HttpOnly` even for Bearer-authenticated requests (harmless). No `Token-Expired`, `WWW-Authenticate` or `Cache-Control` header is set on 401 (searched, not found).
- MFA: `MfaRequired` → `api.context.mfa_required.app_error` is **403**, not 401, and never applies to bots (§1).

## 6. Events emitted on revocation / logout, and what the webapp does

Server: **no WebSocket event announces a revocation or logout.** `RevokeSession*` only sends the mobile wipe push (§3). The events that do fire around the causes in §9 are side effects:

- `PUT /users/{id}/active` → `App.UpdateActive`: `if !active { RevokeAllSessions(); userDeactivated() }` then `sendUpdatedUserEvent` publishes `user_updated` (three sanitisation variants), and the API handler additionally publishes `user_activation_status_change` with empty data to everyone (https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/user.go, https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/api4/user.go). Ordering matters: the sessions are revoked *before* the events are published, so the affected bot's own socket is already de-authenticated (`user.DeleteAt != 0` blocks the PAT fallback) and `ShouldSendEvent` drops both events for it. **Other** connected bots do see `user_updated` with `delete_at != 0` for the victim.
- Disabling a bot (`updateBotActive` → `App.UpdateBotActive` → `UpdateActive(user, false)`) is the same path; tokens are only deleted (`UserAccessToken().DeleteAllForUser`) on permanent bot deletion (https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/bot.go).
- MFA activate/deactivate → `InvalidateCacheForUser` → `InvalidateChannelCacheForUser` → `invalidateWebConnSessionCacheForUser` (hub invalidation, session re-read succeeds, connection continues). Password change with `TerminateSessionsOnPasswordChange` revokes sessions (§3) — no dedicated event.
- Logout (`POST /users/logout`): `RemoveSessionCookie` + `RevokeSessionById(current)`; no event.

Webapp (reference client behaviour):

- The TS websocket client only logs `msg.error` on a `seq_reply` and never inspects `error.id`; the 30 s app-level ping closes with `4000` when a pong callback did not run — but the `not_authenticated` reply *does* invoke the seq callback, so a de-authenticated socket does **not** trip the webapp's pong timeout (https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/platform/client/src/websocket.ts). Our client must inspect `status`/`error.id`, not just "a reply arrived".
- Logout is driven by REST: `forceLogoutIfNecessary` in mattermost-redux — `if err.status_code === 401 && err.url.indexOf('/login') === -1 && currentUserId { Client4.setToken(''); dispatch(LOGOUT_SUCCESS) }` — is called from every `bindClientFunc` catch block (https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/channels/src/packages/mattermost-redux/src/actions/helpers.ts). `emitUserLoggedOutEvent` then dispatches `logout()`, `WebsocketActions.close()`, clears the cookie and redirects (https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/channels/src/actions/global_actions.tsx). `handleClose` in `websocket_actions.ts` only records `WEBSOCKET_FAILURE`; `reconnect()` re-fetches teams/channels/members/posts — any of which 401s and triggers the logout above. `handleUserActivationStatusChange` only refreshes admin analytics on Cloud. (`client4.ts` itself could not be read past truncation; its `ClientError` fields `status_code`, `server_error_id`, `url` are inferred from consumers — unverified.)

## 7. Cluster / HA propagation

Sources: https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/cluster_message.go, https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/cluster_handlers.go

Constants: `ClusterEventClearSessionCacheForUser = "clear_session_user"`, `ClusterEventClearSessionCacheForAllUsers = "inv_all_user_sessions"`, `ClusterEventInvalidateWebConnCacheForUser = "inv_user_teams"`, `ClusterEventInvalidateCacheForUser = "inv_user"`, `ClusterSendReliable = "reliable"`, `ClusterSendBestEffort = "best_effort"`. Two messages travel after a revocation:

1. `clear_session_user` — **reliable** — handler `clusterClearSessionCacheForUserHandler` → `ClearSessionCacheForUserSkipClusterSend(userID)` → local session-cache purge **and** `hub.InvalidateUser(userID)` on that node. This is the one that matters for a socket held by another node.
2. `inv_user_teams` — **best effort** — handler → `invalidateWebConnSessionCacheForUserSkipClusterSend` (hub only). It is sent by `InvalidateChannelCacheForUser`/`InvalidateCacheForUserTeams`, i.e. membership/MFA changes, not by revocation itself.

`ClusterEventInvalidateCacheForUser` (`inv_user`) is not registered in either `platform/cluster_handlers.go` or `app/cluster_handlers.go` on master (both files listed); treat it as legacy. Without a cluster (`clusterIFace == nil`) everything is local and synchronous: `hub.InvalidateUser` blocks on the hub's channel until the hub goroutine picks it up, so on the revoking node the connection is invalidated before the REST revoke call returns. Cross-node latency depends on the enterprise cluster transport and is **unverified** (no timing documented in the public tree); the reliable send type means delivery, not speed. Worst case if a node misses `inv_user_teams` but gets `clear_session_user`: none (the latter does both). Worst case if a node were to miss `clear_session_user`: its `sessionCache` entry lives up to `SessionCacheInMinutes = 10` and the WebConn keeps its 100-year `sessionExpiresAt` — the socket would stay live until reconnect. Plan the REST probe as the backstop for that.

## 8. Comparison: Slack, Discord, Telegram

| Platform | Signal on auth loss | Client classification |
|---|---|---|
| Slack Socket Mode | Envelope `{"type":"disconnect","reason":"link_disabled"}` when Socket Mode is toggled off; `"warning"` ~10 s before a drop; `"refresh_requested"` for routine URL rotation ("you'll need to handle connection refreshes once every few hours"). Re-connect by calling `apps.connections.open`; that call fails with `invalid_auth` ("The provided app-level token wasn't valid."), `token_revoked`, `token_expired`, `account_inactive`. (https://docs.slack.dev/apis/events-api/using-socket-mode, https://docs.slack.dev/reference/methods/apps.connections.open) | `refresh_requested`/`warning` → reconnect; `link_disabled` or an auth error from `apps.connections.open` → fatal, stop retrying. Detection is at reconnect time, not on the open socket. |
| Discord Gateway | Close code `4004 Authentication failed` ("The account token sent with your identify payload is incorrect.", Reconnect: false), `4014 Disallowed intent(s)` (Reconnect: false); "you should consider some close codes as a signal to stop reconnecting. This can be because your token expired, or your identification is invalid." (https://docs.discord.com/developers/topics/opcodes-and-status-codes) | Explicit close frame with a fatal code table — the ideal. |
| Telegram Bot API | Long polling; any failure is `{"ok":false,"error_code":…,"description":…}` ("An Integer 'error_code' field is also returned, but its contents are subject to change") (https://core.telegram.org/bots/api#making-requests). The `401 Unauthorized` on a revoked token is not spelled out in the docs — unverified from primary sources, known from practice. | Clients treat 401 as fatal, 409 (another `getUpdates`) as configuration conflict, 5xx/429 as retry. |
| Mattermost | Nothing on the socket. Silent + `not_authenticated` on any request; REST 401 `api.context.session_expired.app_error`. | Must be synthesised client-side (§11). |

Mattermost is the outlier: it has no fatal close code and no auth-loss event, so the gateway has to build the Discord-style "fatal vs retry" classification from the JSON `ping` reply and a REST probe.

## 9. Timeline per cause

Assumes the bot authenticates with a **personal access token** (the aiommbot case). "Socket" = the bot's own open WebSocket; "REST" = the next `APISessionRequired` call with the same token. Times are server-side, before any client probe.

| Cause | What the server does | Socket | REST |
|---|---|---|---|
| Admin revokes one session (`/sessions/revoke`) or all (`/sessions/revoke/all`), user "logout everywhere", `TerminateSessionsOnPasswordChange` after a password change | Session row(s) removed, session cache cleared, `hub.InvalidateUser` (local now, other nodes via reliable cluster msg) | Stays open. Next broadcast/request re-reads: **PAT fallback recreates the session** → connection continues as if nothing happened (one DB round-trip, no event loss). | Same: 200. Effectively **a no-op for PATs**. |
| `POST /users/logout` with the PAT | `RevokeSessionById(current)` | As above — self-healing. | 200 afterwards. |
| PAT deleted (`/users/tokens/revoke`) or disabled (`/users/tokens/disable`) | Token row deleted/`IsActive=false`, then `RevokeSession(session)` → hub invalidation | Stays open, **no close frame, no event**. Next `IsAuthenticated()` fails (`inactive_token` / not found), token wiped → silent; every JSON request answered `FAIL` / `not_authenticated` (401). | `401 api.context.session_expired.app_error` until re-enabled (disable) or forever (revoke). |
| Bot disabled / user deactivated (`PUT /users/{id}/active false`, `POST /bots/{id}/disable`) | `RevokeAllSessions` + `DeleteAt` set; then `user_updated` + `user_activation_status_change` published to *others* | Open and silent; the bot never sees the events about itself (dropped by `ShouldSendEvent`). Fallback blocked by `inactive_user_id`. | `401 session_expired`. Re-enable restores the same token ("tokens are preserved and will work again if the account is reactivated"). |
| `EnableUserAccessTokens` switched off | Config change | Unaffected for **bot** users (`!user.IsBot` guard); non-bot PAT connections go silent at next re-read. | Bot: 200; non-bot: 401 (`SessionRequired` → `UserAccessToken`). |
| Session expiry (login-session token, not PAT) | Nothing happens server-side; the WebConn's `sessionExpiresAt` passes | Silent from `ExpiresAt` on (`GetSession` → "session is either nil or expired"). Idle timeout (`SessionIdleTimeoutInMinutes`) is checked only on a re-read. | 401 `session_expired`. PATs: never (100-year expiry). |
| Password change (PAT) | Sessions revoked if `TerminateSessionsOnPasswordChange`; MFA change → `InvalidateCacheForUser` | Self-healing (PAT fallback) / re-read succeeds. | 200. |
| MFA enforcement turned on | `MFARequired` re-evaluated per check | Bots exempt (`user.IsBot → nil`). | Non-bot PAT: `403 mfa_required`. |
| Sessions of *all* users revoked (`/users/sessions/revoke/all`) or cache purge | `RemoveAllSessions` + `ClearAllUsersSessionCache` → hub `invalidateAll` also **wipes the token** on every WebConn | Open, permanently silent even for PATs (no token left to re-read). | PAT: **200** (fallback recreates a session) — the one case where REST is healthy while the socket is dead. Reconnect fixes it. |
| Server-side close for unrelated reasons (full send queue, read deadline, restart) | `closeAndRemoveConn` / pump exit | Real close frame / TCP close. | 200. Not an auth problem — reconnect with backoff. |

## 10. Detection signals ranked by latency

1. **Close frame / TCP reset** — immediate, but **never** sent for auth loss (only for queue overflow, ping timeout, bad `authentication_challenge`, hub DB error). Treat a close as "retry", not "fatal".
2. **`FAIL` reply to the JSON `ping` with `error.id == api.web_socket_router.not_authenticated.app_error`** — bounded by the ping period (30 s in our design, ≤ 30 s worst case after the server-side invalidation) plus one RTT. Deterministic: the router checks auth before dispatch (§4) and the error reply bypasses `ShouldSendEvent`. This is the primary detector.
3. **`401` on a REST probe** (`GET /api/v4/users/me`) with `id == api.context.session_expired.app_error` — same order of latency as the probe period; also the only signal that works when the socket is not up, and the disambiguator for §9's last-but-one row (REST 200 + WS `not_authenticated` = socket needs reconnect, token is fine).
4. **Silence** (no event, no pong for > pong deadline) — weakest and slowest; overlaps with proxy idle drops (doc 01 §7). Only a hint to run signals 2–3 sooner.
5. **`user_updated` with `delete_at != 0` for our own user id** — theoretically instant, but **not delivered** to the affected connection (§6); useful only if a second, differently authenticated observer exists. Do not design for it.

## 11. Recommendation for the gateway

**Probe loop.** Keep the 30 s JSON `ping` (doc 01 §3) but treat the reply by content, not by arrival: `status == "OK"` → healthy; `status == "FAIL"` with `error.id == not_authenticated` → *auth-lost*; no reply within the next tick → *pong-timeout* (existing `4000` path). Run a REST liveness probe `GET /api/v4/users/me` with the same token on a slower cadence (e.g. every 60–120 s, and immediately on *auth-lost* or *pong-timeout*). This bounds detection at **≤ 30 s + RTT** for every cause in §9, including HA nodes that only received the reliable `clear_session_user` late, and at one REST period for the cache-miss backstop from §7.

**Decision table** (REST result after an *auth-lost* ping or after a close):

| REST probe | Meaning | Action |
|---|---|---|
| `200` | Token valid; only this socket is de-authenticated (revoke-all-users wipe, PAT re-created after a revoke, HA cache skew) | Close the socket ourselves (`1000`), reconnect with a fresh handshake using the **same** token, resume by `connection_id`/`sequence_number`; expect a new `hello` and resync if the id changed. |
| `401` `api.context.session_expired.app_error` | PAT deleted/disabled, bot disabled, user deactivated, or non-bot PAT with tokens disabled | If a token provider can hand out a refreshed token (rotation supported: "automate your integration to cycle its token through the REST API"), **retry exactly once** with the new token; if the retry also 401s, or no provider exists, raise `FatalError(reason=AUTH_REVOKED)` and stop reconnecting — this is the Discord `4004` equivalent. |
| `403` `api.context.mfa_required.app_error` | Non-bot account under MFA enforcement | Fatal (configuration), same handling as 401 but a distinct reason. |
| `5xx` / connection error / `429` | Dependency failure, not auth | Backoff and retry; keep the socket if it is still open. |

Do **not** attempt in-place `authentication_challenge` after `not_authenticated` even though the router would accept it (§4): it re-registers the connection with the hub, which is untested territory. Reconnect instead.

**Idempotency and ordering.** A self-healing PAT revoke costs nothing on the socket, so the gateway must not tear down on the *first* `not_authenticated` if the immediate REST probe returns 200 and a retry ping returns OK — allow one ping retry (≤ 1 s) before reconnecting, to absorb the hub-invalidation → re-read window.

**Logging (never the token).** Log `connection_id`, last `seq`, probe kind, `status`, `error.id`, `status_code`, `X-Request-Id` from the REST response, and — safe by construction — the server's `detailed_error` `token_sha256=<hex>` (it is a digest the server already logs; still do not compute or log our own digest of the raw token, and never log `Authorization`). Redact `message` if it ever contains `{{.Token}}` interpolation (`api.context.invalid_token.error` does; it is not exposed by handlers today but do not trust that).

**Signals.** Expose three typed outcomes from the connection supervisor: `SocketDegraded(cause=not_authenticated|pong_timeout|closed(code))` → internal reconnect; `AuthRefreshed(attempt=1)` when the single token retry succeeded; `FatalError(reason=AUTH_REVOKED|MFA_REQUIRED|TOKENS_DISABLED, server_error_id, request_id)` → stop the runtime, surface to operators (metric + alert), no automatic retry. Count `not_authenticated` replies and REST 401s as metrics with the `server_error_id` label only (bounded cardinality).

**Upstream note for aiommbot.** A framework-level `AuthLossDetector` (ping-reply inspection + REST probe + the decision table above) belongs in the shared client, not in individual bots; the TS reference client demonstrably lacks it (it only `console.log`s the error), so nothing can be copied from upstream.

## Sources

Server (github.com/mattermost/mattermost, master, fetched 2026-09-03):
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_conn.go — constants, `IsAuthenticated`, `IsBasicAuthenticated`, `IsMFAAuthenticated`, `InvalidateCache`, `ShouldSendEvent`, `authTicker`, `Close`, binary-frame guard
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_hub.go — `Hub` struct, `invalidateUser`/`invalidateAll`/`register`/`unregister` cases, `closeAndRemoveConn`, `InvalidateCacheForUser`, `InvalidateChannelCacheForUser`, `InvalidateCacheForUserTeams`, `invalidateWebConnSessionCacheForUser`, `HubUnregister`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/cluster_handlers.go — handler registrations, `ClearSessionCacheForUserSkipClusterSend`, `ClearSessionCacheForAllUsersSkipClusterSend`, `invalidateWebConnSessionCacheForUser(SkipClusterSend|AllUsers)`, `InvalidateAllCachesSkipSend`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/websocket_router.go — `ServeWebSocket`, `authentication_challenge`, `not_authenticated`, `returnWebSocketError`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/session.go — `GetSession`, `CreateSession`, `AddSessionToCache`, `ClearUserSessionCache(Local)`, `RevokeSession`, `RevokeAllSessions`, `RevokeSessionsFromAllUsers`, `SetSessionExpireInHours`, `ExtendSessionExpiry`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/session.go — `App.GetSession` (PAT fallback, idle timeout), `createSessionForUserAccessToken`, `RevokeSession(ById)`, `RevokeAllSessions`, `ExtendSessionExpiryIfNeeded`, `GetSessionLengthInMillis`, `CreateUserAccessToken`, `RevokeUserAccessToken`, `DisableUserAccessToken`, `EnableUserAccessToken`, `sendMobileWipeSignal`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/authentication.go — `MFARequired`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/user.go — `UpdateActive`, `UpdatePassword` (`TerminateSessionsOnPasswordChange`), MFA → `InvalidateCacheForUser`, `sendUpdatedUserEvent`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/bot.go — `UpdateBotActive`, token deletion only on permanent delete
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/api4/user.go — routes, `createUserAccessToken`, `revokeSession`, `revokeAllSessions*`, `logout`, `updateUserActive` (+ `user_activation_status_change`)
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/api4/bot.go — no token code
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/web/handlers.go — session check, 401 construction, headers
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/web/context.go — `SessionRequired`, `MfaRequired`, `RemoveSessionCookie`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/session.go — `Session`, `IsExpired`, `IsUserAccessToken`, `IsBotUser`, `SessionUserAccessTokenExpiryHours`, `SessionCacheSize`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/config.go — session settings and defaults; absence of a PAT session-length setting
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/cluster_message.go — cluster event constants and send types
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/utils.go — `AppError` json shape, `WipeDetailed`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/websocket_client.go — Go client response dispatch, `Close`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_hub_test.go — `TestHubSessionRevokeRace`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_conn_test.go — `TestWebConnRejectBinaryFrameUnauthenticated`; no expiry tests
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/i18n/en.json — error texts (`api.context.*`; `api.web_socket_router.*` past truncation)

Webapp:
- https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/platform/client/src/websocket.ts — `seq_reply` handling, ping/pong
- https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/channels/src/packages/mattermost-redux/src/actions/helpers.ts — `forceLogoutIfNecessary`
- https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/channels/src/actions/global_actions.tsx — `emitUserLoggedOutEvent`
- https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/channels/src/actions/websocket_actions.ts — `handleClose`, `reconnect`, `handleUserActivationStatusChange`, `handleUserUpdatedEvent`

Docs and other platforms:
- https://developers.mattermost.com/integrate/reference/personal-access-token/ — PATs do not expire; deletion/deactivation semantics; token cycling
- https://docs.slack.dev/apis/events-api/using-socket-mode — `disconnect` reasons
- https://docs.slack.dev/reference/methods/apps.connections.open — `invalid_auth`, `token_revoked`, `token_expired`, `account_inactive`
- https://docs.discord.com/developers/topics/opcodes-and-status-codes — close codes 4004/4014, "stop reconnecting"
- https://core.telegram.org/bots/api#making-requests — `ok:false` / `error_code`

Not reachable / unverified: docs.mattermost.com session-length page (redirect/404 and truncation — config.go used instead); `client4.ts` 401 handling (file truncated); i18n text of `api.web_socket_router.not_authenticated.app_error`; enterprise cluster delivery latency; safety of re-`HubRegister` via a second `authentication_challenge`; whether any API path sets `UserAccessToken.ExpiresAt`.
