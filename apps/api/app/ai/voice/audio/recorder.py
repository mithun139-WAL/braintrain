import wave

class AudioRecorder:
    def __init__(self, room_name: str):
        """
        Manages the internal PCM buffer and exports it to a WAV file.
        
        :param room_name: The room name used to prefix the temporary WAV file.
        """
        self.room_name = room_name
        self._buffer = bytearray()
        self._is_recording = False
        self._sample_rate = 16000
        self._num_channels = 1

    def start(self, sample_rate: int = 16000, num_channels: int = 1) -> None:
        """Starts recording and clears any previous frames."""
        self._is_recording = True
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self.reset()

    def append(self, frame_data: bytes) -> None:
        """Appends raw PCM audio bytes to the buffer if recording is active."""
        if self._is_recording:
            self._buffer.extend(frame_data)

    def stop(self) -> bytes:
        """Stops recording and returns the captured PCM data."""
        self._is_recording = False
        return bytes(self._buffer)

    def reset(self) -> None:
        """Clears the internal audio buffer."""
        self._buffer.clear()

    def export_wav(self) -> str:
        """
        Writes the internal PCM buffer into a temporary WAV file.
        
        :return: Path to the temporary WAV file.
        """
        temp_input = f"temp_input_{self.room_name}.wav"
        with wave.open(temp_input, "wb") as wf:
            wf.setnchannels(self._num_channels)
            wf.setsampwidth(2)  # signed 16-bit PCM has sample width of 2 bytes
            wf.setframerate(self._sample_rate)
            wf.writeframes(bytes(self._buffer))
        return temp_input
