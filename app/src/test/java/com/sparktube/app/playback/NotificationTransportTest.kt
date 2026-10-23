package com.sparktube.app.playback

import androidx.media3.common.Player
import org.junit.Assert.*
import org.junit.Test
import java.lang.reflect.Proxy

class NotificationTransportTest {
    private class FakePlayer(
        var ready: Boolean = true,
        var state: Int = Player.STATE_READY
    ) {
        val calls = mutableListOf<String>()
        val unavailable = mutableSetOf<Int>()
        val player = Proxy.newProxyInstance(Player::class.java.classLoader, arrayOf(Player::class.java)) { _, method, args ->
            when (method.name) {
                "getPlayWhenReady" -> ready
                "getPlaybackState" -> state
                "isCommandAvailable" -> args!![0] !in unavailable
                "pause" -> { calls += "pause"; ready = false; null }
                "play" -> { calls += "play"; ready = true; null }
                "prepare" -> { calls += "prepare"; null }
                "seekToDefaultPosition" -> { calls += "restart"; null }
                else -> error("Unexpected player access: ${method.name}")
            }
        } as Player
        fun tap(notification: Boolean = true, action: Int = 0, key: Int = 85, repeat: Int = 0) =
            NotificationTransport.handle(player, notification, action, key, repeat)
    }

    @Test fun firstTapPausesSynchronously() {
        val p = FakePlayer()
        assertTrue(p.tap())
        assertFalse(p.ready)
        assertEquals(listOf("pause"), p.calls)
    }
    @Test fun firstTapResumesSynchronously() {
        val p = FakePlayer(ready = false)
        assertTrue(p.tap())
        assertTrue(p.ready)
        assertEquals(listOf("play"), p.calls)
    }
    @Test fun rapidSeparateTapsEachToggleWithoutSkippingOrWaiting() {
        val p = FakePlayer()
        repeat(6) { assertTrue(p.tap()) }
        assertTrue(p.ready)
        assertEquals(listOf("pause", "play", "pause", "play", "pause", "play"), p.calls)
    }
    @Test fun bufferingPauseUsesIntentAndDoesNotPrepareOrRestart() {
        val p = FakePlayer(state = Player.STATE_BUFFERING)
        assertTrue(p.tap())
        assertFalse(p.ready)
        assertEquals(listOf("pause"), p.calls)
        assertTrue(p.tap())
        assertEquals(listOf("pause", "play"), p.calls)
    }
    @Test fun headsetKeepsNativeDoubleTapHandling() {
        val p = FakePlayer()
        assertFalse(p.tap(notification = false))
        assertTrue(p.calls.isEmpty())
    }
    @Test fun keyUpAndOtherKeysAreNotIntercepted() {
        val p = FakePlayer()
        assertFalse(p.tap(action = 1))
        for (key in listOf(79, 86, 87, 88, 126, 127)) assertFalse(p.tap(key = key))
        assertTrue(p.calls.isEmpty())
    }
    @Test fun heldRepeatIsConsumedWithoutSecondToggle() {
        val p = FakePlayer()
        assertTrue(p.tap())
        assertTrue(p.tap(repeat = 1))
        assertTrue(p.tap(repeat = 2))
        assertEquals(listOf("pause"), p.calls)
    }
    @Test fun unavailablePlayPauseCannotBypassCommandAvailability() {
        val p = FakePlayer()
        p.unavailable += Player.COMMAND_PLAY_PAUSE
        assertTrue(p.tap())
        assertTrue(p.calls.isEmpty())
    }
    @Test fun idlePlayPreparesSourceFirst() {
        val p = FakePlayer(ready = false, state = Player.STATE_IDLE)
        assertTrue(p.tap())
        assertEquals(listOf("prepare", "play"), p.calls)
    }
    @Test fun endedPlayRestartsAtDefaultPosition() {
        val p = FakePlayer(state = Player.STATE_ENDED)
        assertTrue(p.tap())
        assertEquals(listOf("restart", "play"), p.calls)
    }
    @Test fun prepareAndSeekRespectAvailableCommands() {
        val idle = FakePlayer(ready = false, state = Player.STATE_IDLE)
        idle.unavailable += Player.COMMAND_PREPARE
        idle.tap()
        assertEquals(listOf("play"), idle.calls)
        val ended = FakePlayer(state = Player.STATE_ENDED)
        ended.unavailable += Player.COMMAND_SEEK_TO_DEFAULT_POSITION
        ended.tap()
        assertEquals(listOf("play"), ended.calls)
    }
}
