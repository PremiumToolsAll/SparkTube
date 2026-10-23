package com.sparktube.app.playback

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoFramePolicyTest {
    @Test fun audioReadyIsNotProofOfVideo() {
        assertEquals(VideoFramePolicy.Action.REBIND_OUTPUT,
            VideoFramePolicy.action(8_000, false, 0))
    }
    @Test fun noPrematureRecovery() {
        assertEquals(VideoFramePolicy.Action.WAIT,
            VideoFramePolicy.action(7_999, false, 0))
    }
    @Test fun firstFrameStopsAllRecovery() {
        for (step in 0..5) {
            assertEquals(VideoFramePolicy.Action.WAIT,
                VideoFramePolicy.action(Long.MAX_VALUE, true, step))
        }
    }
    @Test fun recoveryIsBoundedAndOrdered() {
        assertEquals(VideoFramePolicy.Action.REBIND_OUTPUT, VideoFramePolicy.action(8_000, false, 0))
        assertEquals(VideoFramePolicy.Action.RETRY_SOURCE, VideoFramePolicy.action(8_000, false, 1))
        assertEquals(VideoFramePolicy.Action.SHOW_ERROR, VideoFramePolicy.action(8_000, false, 2))
        assertEquals(VideoFramePolicy.Action.SHOW_ERROR, VideoFramePolicy.action(Long.MAX_VALUE, false, 3))
    }
}
