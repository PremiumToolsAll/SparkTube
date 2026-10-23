package com.sparktube.app.playback

/** Video app-queue boundaries, independent of Android and stream resolution. */
internal object QueueNavigationPolicy {
    fun hasCurrent(index: Int, size: Int): Boolean = size > 0 && index >= 0 && index < size
    fun hasNext(index: Int, size: Int): Boolean = hasCurrent(index, size) && index < size - 1
    fun hasPrevious(index: Int, size: Int): Boolean = hasCurrent(index, size) && index > 0
}
