import math
import os
import random
import struct
import wave


SAMPLE_RATE = 22050
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT_DIR, "assets", "audio", "synth")


def clamp(value, low=-1.0, high=1.0):
    return max(low, min(high, value))


def write_wav(filename, samples):
    os.makedirs(OUT_DIR, exist_ok=True)
    peak = max(0.01, max(abs(s) for s in samples))
    gain = min(1.0, 0.92 / peak)
    path = os.path.join(OUT_DIR, filename)
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        data = bytearray()
        for sample in samples:
            data.extend(struct.pack("<h", int(clamp(sample * gain) * 32767)))
        handle.writeframes(data)


def mix(base, overlay, start=0):
    if start + len(overlay) > len(base):
        base.extend([0.0] * (start + len(overlay) - len(base)))
    for i, sample in enumerate(overlay):
        base[start + i] += sample
    return base


def sine(freq, t):
    return math.sin(math.tau * freq * t)


def square(freq, t):
    return 1.0 if sine(freq, t) >= 0 else -1.0


def saw(freq, t):
    return 2.0 * ((freq * t) % 1.0) - 1.0


def gunshot(duration, body_freq, crack_freq, power=1.0, seed=1, thump=1.0):
    rng = random.Random(seed)
    total = int(duration * SAMPLE_RATE)
    samples = []
    noise_state = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        env_fast = math.exp(-t * 28)
        env_body = math.exp(-t * 9)
        env_tail = math.exp(-t * 5)
        noise_state = noise_state * 0.62 + rng.uniform(-1, 1) * 0.38
        pitch_drop = max(0.35, 1.0 - t * 2.1)
        sample = noise_state * env_fast * 0.95
        sample += sine(body_freq * pitch_drop, t) * env_body * 0.72 * thump
        sample += square(crack_freq, t) * env_fast * 0.24
        sample += rng.uniform(-1, 1) * env_tail * 0.12
        samples.append(sample * power)
    return samples


def double_tap():
    base = [0.0] * int(0.34 * SAMPLE_RATE)
    mix(base, gunshot(0.19, 175, 2450, 0.78, 11, 0.72), 0)
    mix(base, gunshot(0.19, 182, 2520, 0.78, 12, 0.72), int(0.064 * SAMPLE_RATE))
    return base


def laser_shot():
    total = int(0.42 * SAMPLE_RATE)
    samples = []
    rng = random.Random(21)
    for i in range(total):
        t = i / SAMPLE_RATE
        pct = t / 0.42
        env = math.sin(min(1, pct) * math.pi) * math.exp(-t * 1.6)
        freq = 520 + 1680 * pct
        pulse = 0.5 + 0.5 * sine(36, t)
        sample = sine(freq, t) * env * 0.54
        sample += sine(freq * 1.51, t) * env * 0.18
        sample += rng.uniform(-1, 1) * env * 0.05 * pulse
        samples.append(sample)
    return samples


def railbreaker_shot():
    total = int(0.58 * SAMPLE_RATE)
    samples = [0.0] * total
    rng = random.Random(25)
    charge_len = int(0.14 * SAMPLE_RATE)
    blast_start = int(0.10 * SAMPLE_RATE)
    for i in range(total):
        t = i / SAMPLE_RATE
        sample = 0.0
        if i < charge_len:
            pct = i / max(1, charge_len)
            env = pct * pct
            sample += sine(220 + 1280 * pct, t) * env * 0.22
            sample += sine(440 + 2100 * pct, t) * env * 0.08
        if i >= blast_start:
            local = (i - blast_start) / SAMPLE_RATE
            env_fast = math.exp(-local * 22)
            env_body = math.exp(-local * 5.4)
            crack = square(3100, local) * env_fast * 0.28
            thump = sine(64 * max(0.4, 1 - local * 2.8), local) * env_body * 0.96
            coil = sine(760 + 220 * math.exp(-local * 7), local) * env_body * 0.24
            noise = rng.uniform(-1, 1) * env_fast * 0.58
            sample += crack + thump + coil + noise
        samples[i] = sample
    return samples


def reload_click():
    total = int(0.62 * SAMPLE_RATE)
    samples = [0.0] * total
    rng = random.Random(41)
    for offset, amp, tone in [(0.02, 0.62, 900), (0.16, 0.48, 660), (0.36, 0.52, 1180)]:
        start = int(offset * SAMPLE_RATE)
        length = int(0.085 * SAMPLE_RATE)
        for i in range(length):
            t = i / SAMPLE_RATE
            env = math.exp(-t * 35)
            samples[start + i] += (square(tone, t) * 0.32 + rng.uniform(-1, 1) * 0.68) * env * amp
    return samples


def rising_chime(duration=1.05, seed=51):
    total = int(duration * SAMPLE_RATE)
    samples = []
    rng = random.Random(seed)
    notes = [523.25, 659.25, 783.99, 1046.5, 1318.5]
    for i in range(total):
        t = i / SAMPLE_RATE
        env = math.sin(min(1, t / duration) * math.pi) ** 0.45
        sample = 0.0
        for n, freq in enumerate(notes):
            start = n * 0.12
            if t >= start:
                local = t - start
                sample += sine(freq, local) * math.exp(-local * 3.6) * 0.28
                sample += square(freq * 2, local) * math.exp(-local * 5.4) * 0.04
        sample += rng.uniform(-1, 1) * env * 0.015
        samples.append(sample)
    return samples


def upgrade_swell():
    total = int(1.12 * SAMPLE_RATE)
    samples = []
    rng = random.Random(61)
    for i in range(total):
        t = i / SAMPLE_RATE
        pct = t / 1.12
        rise = min(1.0, pct * 1.4)
        env = math.sin(min(1, pct) * math.pi)
        sample = sine(180 + 520 * rise, t) * env * 0.32
        sample += sine(360 + 920 * rise, t) * env * 0.20
        sample += rng.uniform(-1, 1) * env * 0.045
        if pct > 0.72:
            sample += square(1400, t) * math.exp(-(pct - 0.72) * 12) * 0.22
        samples.append(sample)
    return samples


def zombie_voice(kind, duration, seed):
    rng = random.Random(seed)
    total = int(duration * SAMPLE_RATE)
    samples = []
    for i in range(total):
        t = i / SAMPLE_RATE
        pct = t / duration
        env = math.sin(min(1, pct) * math.pi) ** 0.55
        wobble = 1 + 0.14 * sine(4.5 + seed % 5, t) + 0.06 * sine(13, t)
        if kind == "death":
            base = 94 - 46 * pct
            env *= math.exp(-pct * 0.5)
        elif kind == "attack":
            base = 128 + 28 * sine(5.5, t)
            env *= 1.0 - pct * 0.24
        elif kind == "titan":
            base = 44 + 16 * sine(3.0, t)
            env *= 1.15
        else:
            base = 72 + 18 * sine(2.7, t)
        rasp = rng.uniform(-1, 1) * 0.22 + saw(base * 1.7 * wobble, t) * 0.18
        sample = sine(base * wobble, t) * 0.48
        sample += sine(base * 0.5 * wobble, t) * 0.35
        sample += rasp
        samples.append(sample * env)
    return samples


def kick(t):
    return sine(72 * max(0.4, 1 - t * 5), t) * math.exp(-t * 18)


def snare(t, rng):
    return rng.uniform(-1, 1) * math.exp(-t * 24)


def music_loop(name, duration, tempo, root, intensity, seed):
    rng = random.Random(seed)
    total = int(duration * SAMPLE_RATE)
    samples = [0.0] * total
    beat = 60 / tempo
    scale = [0, 3, 5, 7, 10, 12]
    bass_prog = [root, root - 5, root - 2, root - 7]
    for i in range(total):
        t = i / SAMPLE_RATE
        bar = int(t / (beat * 4))
        beat_pos = (t % beat) / beat
        beat_index = int(t / beat)
        root_freq = bass_prog[bar % len(bass_prog)]
        local_beat = t % beat

        sample = 0.0
        if beat_pos < 0.18:
            sample += kick(local_beat) * (0.26 + intensity * 0.17)
        if beat_index % 4 in (1, 3) and beat_pos < 0.16:
            sample += snare(local_beat, rng) * (0.08 + intensity * 0.12)
        if int(t / (beat / 2)) % 2 == 0 and beat_pos < 0.05:
            sample += rng.uniform(-1, 1) * math.exp(-beat_pos * 80) * 0.035 * intensity

        bass_env = math.exp(-local_beat * 1.8)
        sample += sine(root_freq, t) * bass_env * (0.16 + intensity * 0.08)
        sample += square(root_freq * 0.5, t) * bass_env * 0.045

        arp_step = int(t / (beat / 4))
        note_freq = root_freq * (2 ** (scale[arp_step % len(scale)] / 12))
        arp_env = math.exp(-((t % (beat / 4)) / (beat / 4)) * 4)
        sample += square(note_freq * 2, t) * arp_env * (0.035 + intensity * 0.06)

        pad_freq = root_freq * 0.5
        pad = sine(pad_freq, t) + sine(pad_freq * 1.5, t) * 0.45 + sine(pad_freq * 2, t) * 0.25
        sample += pad * (0.035 + intensity * 0.025)
        samples[i] = sample

    fade = int(0.45 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / max(1, fade)
        samples[i] *= factor
        samples[-i - 1] *= factor
    write_wav(name, samples)


def main():
    write_wav("gun_glock17.wav", gunshot(0.24, 158, 2380, 0.78, 1, 0.62))
    write_wav("gun_dual_beretta.wav", double_tap())
    write_wav("gun_mp5.wav", gunshot(0.18, 138, 2750, 0.58, 3, 0.48))
    write_wav("gun_mossberg500.wav", gunshot(0.46, 84, 1760, 1.0, 4, 1.18))
    write_wav("gun_m4a1.wav", gunshot(0.28, 118, 3020, 0.86, 5, 0.82))
    write_wav("gun_benelli_m4.wav", gunshot(0.38, 96, 1980, 0.95, 6, 1.02))
    write_wav("gun_xm_las.wav", laser_shot())
    write_wav("gun_xm_railbreaker.wav", railbreaker_shot())
    write_wav("reload_mag.wav", reload_click())
    write_wav("level_up.wav", rising_chime())
    write_wav("weapon_upgrade.wav", upgrade_swell())
    write_wav("zombie_groan.wav", zombie_voice("groan", 1.25, 71))
    write_wav("zombie_attack.wav", zombie_voice("attack", 0.62, 72))
    write_wav("zombie_death.wav", zombie_voice("death", 0.96, 73))
    write_wav("zombie_titan.wav", zombie_voice("titan", 1.42, 74))
    music_loop("bgm_dead_factory.wav", 24.0, 86, 55, 0.36, 101)
    music_loop("bgm_last_stand.wav", 24.0, 122, 55, 0.72, 102)
    music_loop("bgm_boss_warning.wav", 24.0, 98, 43, 0.92, 103)


if __name__ == "__main__":
    main()
