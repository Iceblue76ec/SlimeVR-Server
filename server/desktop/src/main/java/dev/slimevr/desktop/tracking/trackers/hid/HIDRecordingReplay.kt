package dev.slimevr.desktop.tracking.trackers.hid

import dev.slimevr.tracking.trackers.Tracker
import dev.slimevr.tracking.trackers.hid.HIDCommon
import dev.slimevr.tracking.trackers.hid.HIDDevice
import io.eiren.util.logging.LogManager
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.locks.LockSupport
import java.util.function.Consumer

/** Replays the raw reports made by tools/udp-capture/record-hid.py. */
class HIDRecordingReplay(private val path: String, private val trackersConsumer: Consumer<Tracker>) : Thread("HID recording replay") {
	private val devices = mutableListOf<HIDDevice>()
	private val deviceList = mutableListOf<Int>()
	private val q = IntArray(4)
	private val a = IntArray(3)
	private val m = IntArray(3)

	init { isDaemon = true }

	override fun run() {
		try {
			while (!isInterrupted) {
				var firstTime: Long? = null
				var previousTime: Long? = null
				var start = 0L
				var reports = 0
				File(path).bufferedReader().useLines { lines ->
					lines.forEach { line ->
						if (line.contains("\"type\": \"header\"") || line.contains("\"type\":\"header\"")) return@forEach
						val time = timestampPattern.find(line)?.groupValues?.get(1)?.toLong()
							?: error("Invalid HID recording timestamp")
						val hex = hexPattern.find(line)?.groupValues?.get(1) ?: error("Invalid HID recording report")
						require(hex.length == 128) { "HID report must be 64 bytes" }
						if (previousTime != null) require(time >= previousTime!!) { "HID timestamps are not ordered" }
						if (firstTime == null) { firstTime = time; start = System.nanoTime() }
						previousTime = time
						val deadline = start + (time - firstTime!!)
						while (!isInterrupted) {
							val remaining = deadline - System.nanoTime()
							if (remaining <= 0) break
							LockSupport.parkNanos(remaining)
						}
						if (isInterrupted) return
						val data = ByteArray(64) { i -> hex.substring(i * 2, i * 2 + 2).toInt(16).toByte() }
						for (offset in data.indices step HIDCommon.PACKET_SIZE) {
							val type = data[offset].toUByte().toInt()
							val id = data[offset + 1].toUByte().toInt()
							if (type == 255) {
								val address = ByteBuffer.wrap(data, offset + 2, 8).order(ByteOrder.LITTLE_ENDIAN).long and 0xFFFFFFFFFFFF
								HIDCommon.deviceIdLookup(devices, "recording", id, String.format("%012X", address), deviceList)
							} else {
								val device = HIDCommon.deviceIdLookup(devices, "recording", id, null, deviceList)
								if (device != null) HIDCommon.processPacket(data, offset, type, device, q, a, m, trackersConsumer)
							}
						}
						reports++
					}
				}
				require(reports > 0) { "HID recording contains no reports" }
				LogManager.info("[HID replay] Replayed $reports reports; restarting recording")
			}
		} catch (e: Exception) {
			LogManager.severe("[HID replay] Playback stopped: ${e.message}", e)
		}
	}

	companion object {
		private val timestampPattern = Regex("\"time_unix_ns\"\\s*:\\s*(\\d+)")
		private val hexPattern = Regex("\"hex\"\\s*:\\s*\"([0-9a-fA-F]+)\"")
	}
}
