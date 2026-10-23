package com.sparktube.app.playback

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class QueueNavigationPolicyTest {
    @Test fun emptyQueueHasNoTransportTarget() {
        assertFalse(QueueNavigationPolicy.hasCurrent(-1, 0))
        assertFalse(QueueNavigationPolicy.hasNext(-1, 0))
        assertFalse(QueueNavigationPolicy.hasPrevious(-1, 0))
    }

    @Test fun singleItemCanRestartButCannotSkip() {
        assertTrue(QueueNavigationPolicy.hasCurrent(0, 1))
        assertFalse(QueueNavigationPolicy.hasNext(0, 1))
        assertFalse(QueueNavigationPolicy.hasPrevious(0, 1))
    }

    @Test fun firstItemHasNextButNoPrevious() {
        assertTrue(QueueNavigationPolicy.hasNext(0, 3))
        assertFalse(QueueNavigationPolicy.hasPrevious(0, 3))
    }

    @Test fun middleItemCanSkipBothDirections() {
        assertTrue(QueueNavigationPolicy.hasNext(1, 3))
        assertTrue(QueueNavigationPolicy.hasPrevious(1, 3))
    }

    @Test fun lastItemCannotSkipPastQueueEnd() {
        assertFalse(QueueNavigationPolicy.hasNext(2, 3))
        assertTrue(QueueNavigationPolicy.hasPrevious(2, 3))
    }

    @Test fun unresolvedNegativeIndexDoesNotEnableNext() {
        assertFalse(QueueNavigationPolicy.hasNext(-1, 4))
        assertFalse(QueueNavigationPolicy.hasCurrent(-1, 4))
    }

    @Test fun outOfBoundsIndexCannotSkip() {
        assertFalse(QueueNavigationPolicy.hasNext(4, 4))
        assertFalse(QueueNavigationPolicy.hasPrevious(4, 4))
        assertFalse(QueueNavigationPolicy.hasPrevious(Int.MAX_VALUE, 4))
    }

    @Test fun largeQueueDoesNotOverflow() {
        assertTrue(QueueNavigationPolicy.hasNext(Int.MAX_VALUE - 2, Int.MAX_VALUE))
        assertFalse(QueueNavigationPolicy.hasNext(Int.MAX_VALUE - 1, Int.MAX_VALUE))
        assertFalse(QueueNavigationPolicy.hasNext(Int.MAX_VALUE, Int.MAX_VALUE))
    }
}
