package com.sparktube.app.playback

import androidx.media3.common.Player
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test
import java.lang.reflect.Proxy

class PlayerListenerBridgeTest {
    @Test fun everyMedia3CallbackIsExplicitlyForwarded() {
        val received = mutableListOf<java.lang.reflect.Method>()
        val delegate = Proxy.newProxyInstance(Player.Listener::class.java.classLoader,
            arrayOf(Player.Listener::class.java)) { _, method, _ -> received.add(method); null } as Player.Listener
        val bridge = PlayerListenerBridge(delegate)
        val callbacks = Player.Listener::class.java.declaredMethods.filter { it.name.startsWith("on") }
        assertEquals(37, callbacks.size)
        for (callback in callbacks) {
            assertNotNull(PlayerListenerBridge::class.java.getDeclaredMethod(callback.name, *callback.parameterTypes))
            val args = callback.parameterTypes.map { type ->
                when (type) {
                    java.lang.Boolean.TYPE -> false
                    java.lang.Integer.TYPE -> 0
                    java.lang.Long.TYPE -> 0L
                    java.lang.Float.TYPE -> 0f
                    else -> null
                }
            }.toTypedArray()
            callback.invoke(bridge, *args)
            assertEquals(callback, received.last())
        }
        assertEquals(callbacks.size, received.size)
    }

    @Test fun firstFrameTracksAndSizeReachTheDelegate() {
        val received = mutableListOf<String>()
        val delegate = Proxy.newProxyInstance(Player.Listener::class.java.classLoader,
            arrayOf(Player.Listener::class.java)) { _, method, _ -> received.add(method.name); null } as Player.Listener
        val bridge = PlayerListenerBridge(delegate)
        bridge.onRenderedFirstFrame()
        for (name in listOf("onTracksChanged", "onVideoSizeChanged")) {
            Player.Listener::class.java.declaredMethods.first { it.name == name }
                .invoke(bridge, *arrayOfNulls<Any>(1))
        }
        assertEquals(listOf("onRenderedFirstFrame", "onTracksChanged", "onVideoSizeChanged"), received)
    }

    @Test fun reproducesOldKotlinDelegationBlackShutterBug() {
        var frameCalls = 0
        val target = object : Player.Listener {
            override fun onRenderedFirstFrame() { frameCalls++ }
        }
        // Under the project's current Kotlin compiler, Java-default methods are NOT forwarded by `by`.
        val oldBrokenBridge = object : Player.Listener by target {}
        oldBrokenBridge.onRenderedFirstFrame()
        assertEquals(0, frameCalls)
        PlayerListenerBridge(target).onRenderedFirstFrame()
        assertEquals(1, frameCalls)
    }
}
