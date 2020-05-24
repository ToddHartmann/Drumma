# DruMMA
### Version 1.0.1

Turn the drum track from a MIDI clip into [MMA - Musical MIDI Accompaniment](https://mellowood.ca/mma/) code.

### Installation

1.  Put drumma.py in your Python Scripts directory.

2.  DruMMA is a command line app and requires only 
[Peter Billam's elegant MIDI.py](http://www.pjb.com.au/midi/free/MIDI.py)
([github](https://github.com/peterbillam/miditools/blob/master/MIDI.py)).
Put "MIDI.py" in your site-packages.

### Examples

#### 4:4
Running DruMMA on this [short MIDI clip](four-clip.mid) ([audio](four-clip.mp3))
 (kick 1234, snare 2&4, hat eighths)
produces [the following MMA code](four-drums.mma):

<pre>
// MMA text produced by drumma.py
// W:\Drumma\drumma.py four-clip.mid -o four-drums.mma
TEMPO 120
TIMESIG 4/4
TIME 4.0
SEQSIZE 1
BEGIN Drum-KickDrum1
  TONE KickDrum1
  BEGIN DEFINE
    KickDrum1M1  1.000 192t 64;  2.000 192t 64;  3.000 192t 64;  4.000 192t 64;
  END
  SEQUENCE  KickDrum1M1
END
BEGIN Drum-SnareDrum1
  TONE SnareDrum1
  BEGIN DEFINE
    SnareDrum1M1  2.000 192t 64;  4.000 192t 64;
  END
  SEQUENCE  SnareDrum1M1
END
BEGIN Drum-ClosedHiHat
  TONE ClosedHiHat
  BEGIN DEFINE
    ClosedHiHatM1  1.000 96t 64;  1.500 96t 64;  2.000 96t 64;  2.500 96t 64;  3.000 96t 64;  3.500 96t 64;  4.000 96t 64;  4.500 96t 64;
  END
  SEQUENCE  ClosedHiHatM1
END
REPEAT
    E
REPEATEND NOWARN 1
</pre>

Which renders [this MIDI](four-drums.mid) ([audio](four-drums.mp3)).

Each drum instrument gets a BEGIN...END block.  Each measure gets DEFINEd with a name and rhythm.  The names are added to the SEQUENCE.  After the BEGIN...END blocks there is a an E chord with enough repeats to play the SEQUENCEs.  You copy the measures you want into your own compositions.  Enjoy!

#### Rainbow, "Stargazer" drum intro by Cozy Powell

DruMMA can be used for longer sections!

Here is a [longer MIDI clip](stargazer-clip.mid) ([audio](stargazer-clip.mp3)).
Let me tell you right now, DruMMA won't transcribe those lovely effects.
But it made [this MMA code](stargazer-drums.mma),
which renders to [this MIDI](stargazer-drums.mid) ([audio](stargazer-drums.mp3)).
Saves a lot of listening and typing.

#### Rush, "Tom Sawyer" drum fill by Neil Peart

No drum demo is complete without **The Fill** from [Tom Sawyer](sawyer-clip.mid) ([audio](sawyer-clip.mp3)).
DruMMA makes [this MMA code](sawyer-drums.mma).
That code renders to [this MIDI](sawyer-drums.mid)
which sounds like [this](sawyer-drums.mp3).

## The Help
<pre>
usage: drumma.py input.mid [-h] [-o OUTPUT] [-z] [-qt DENOM] [-qv NUM] [-p PLACES] [-c CHANNEL] [-m] [-r]

DruMMA: Turn General MIDI drum measures into MMA-Musical MIDI
Accompaniment code. Version 1.0.1.

positional arguments:
  input                 MIDI file to process

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file (if "-" or not set, just print the output)
  -z, --zero            Force all durations to "0" like BvdP does
  -qt DENOM, --quant_time DENOM
                        Quantize note starts and durations to the nearest
                        1/DENOM (4 means quarter, 8 means 8th, etc.). DENOM is
                        a positive integer less than 10000, default = 32 (32nd
                        notes), 0 for no quantization
  -qv NUM, --quant_vel NUM
                        Quantize velocities to the center of each NUM-width
                        velocity step (if NUM=4, centers are 2,6,10, etc.).
                        NUM is a positive integer less than 128, default = 0 =
                        no quantization
  -p PLACES, --places PLACES
                        Number of places (between 0 and 12) to include after
                        the decimal point (default 3)
  -c CHANNEL, --channel CHANNEL
                        MIDI Channel to find drum events on (0=all,
                        default=10)
  -m, --mute            Suppress commentary lines
  -r, --repeat          Repeat identical lines (don't factor)

Trim your MIDI to just the drum measures you want. Your MIDI clip
should have only one tempo and only one time signature.
</pre>
