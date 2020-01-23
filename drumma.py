# -*- coding: utf-8 -*-
__version__ = '1.0.1'
"""
DruMMA

Turn the drum track from a MIDI clip into MMA - Musical MIDI Accompaniment,
a fantastic composition tool by Bob van der Poel.

Author:  Todd Hartmann
License:  Public Domain, Use At Your Own Risk

Installation:
    Put this file ("drumma.py") in your Python Scripts directory.

    DruMMA is a command line app and requires only Peter Billam's elegant
    MIDI.py

    https://github.com/peterbillam/miditools/blob/master/MIDI.py
     -or-
    http://www.pjb.com.au/midi/free/MIDI.py

    Put "MIDI.py" in your site-packages.

MMA-Musical MIDI Accompaniment Site:
    https://mellowood.ca/mma/
"""
import MIDI                   # http://www.pjb.com.au/midi/free/MIDI.py
import io, sys
import argparse, textwrap
import contextlib
from collections import namedtuple

sys.tracebacklimit = None   # kludgey solution to uselessly long stack traces

def fillit(s): return textwrap.fill(' '.join(s.split()))

# MMA Reference Manual, "Drum Notes, by MIDI Value"
def getnames():
    return( {27: 'HighQ', 28: 'Slap', 29: 'ScratchPush', 30: 'ScratchPull', \
             31: 'Sticks', 32: 'SquareClick', 33: 'MetronomeClick', 34: 'MetronomeBell', \
             35: 'KickDrum2', 36: 'KickDrum1', 37: 'SideKick', 38: 'SnareDrum1', \
             39: 'HandClap', 40: 'SnareDrum2', 41: 'LowTom2', 42: 'ClosedHiHat', \
             43: 'LowTom1', 44: 'PedalHiHat', 45: 'MidTom2', 46: 'OpenHiHat', \
             47: 'MidTom1', 48: 'HighTom2', 49: 'CrashCymbal1', 50: 'HighTom1', \
             51: 'RideCymbal1', 52: 'ChineseCymbal', 53: 'RideBell', 54: 'Tambourine', \
             55: 'SplashCymbal', 56: 'CowBell', 57: 'CrashCymbal2', 58: 'VibraSlap', \
             59: 'RideCymbal2', 60: 'HighBongo', 61: 'LowBongo', 62: 'MuteHighConga', \
             63: 'OpenHighConga', 64: 'LowConga', 65: 'HighTimbale', 66: 'LowTimbale', \
             67: 'HighAgogo', 68: 'LowAgogo', 69: 'Cabasa', 70: 'Maracas', \
             71: 'ShortHiWhistle', 72: 'LongLowWhistle', 73: 'ShortGuiro', 74: 'LongGuiro', \
             75: 'Claves', 76: 'HighWoodBlock', 77: 'LowWoodBlock', 78: 'MuteCuica', \
             79: 'OpenCuica', 80: 'MuteTriangle', 81: 'OpenTriangle', 82: 'Shaker', \
             83: 'JingleBell', 84: 'Castanets', 85: 'MuteSudro', 86: 'OpenSudro'} )
#
class TimeSig:
    def __init__(self, ndcb = [ 4, 2, 24, 8 ] ):
        self.n = ndcb[0]    # time sig numerator
        self.d = ndcb[1]    # time sig denominator
        self.c = ndcb[2]    # IGNORED # MIDI clocks between metronome clicks (clocks are not ticks!)
        self.b = ndcb[3]    # IGNORED # number of notated 32nd-notes in a MIDI quarter-note (24 MIDI Clocks)

    def __str__(self):
        return( 'TimeSig: n {0} / d {1}, c {2}, b {3}'.format(self.n, self.d, self.c, self.b) )
#
# https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Metas(metaclass=Singleton):
    def __init__(self):
        self.timesig = TimeSig()
        self.name = ''
        self.tempo = 500000     # Aggie tempo
        self.ticks = 192
        self.lastevent = 0      # time of last drum event

    def __str__(self):
        return('Name: {0}\nTempo: {1}\nTicks: {2}\nLast Time: {3}\n{4}'.format(
                                self.name, (1000000 / self.tempo) * 60,
                                self.ticks, self.lastevent, self.timesig) )

    def updlast(self, val):
        if val > self.lastevent:
            self.lastevent = val

    def beatsperq(self):
        """Return # of beats per quarter (4/4 = 1, 6/8 = 2, 15/16 = 4, etc.)"""
        bpq = pow(2, self.timesig.d) / 4    # '4' is constant for 'quarter note'
        return bpq
#
    def qpermeas(self):
        """Return # of Quarter notes Per Measure"""
        num = self.timesig.n
        bpq = self.beatsperq()
        qpm = num / bpq                  # quarters per measure
        return qpm

    def measlen(self):
        """Return the length of a measure in midi file's ticks"""
        return self.qpermeas() * self.ticks

    def lastmeas(self):
        """Return a human musician-friendly 1-based last measure number"""
        return( int(self.lastevent / self.measlen()) + 1 )

    def ticks2mma(self, val):
        """MIDI file's PPQN to MMA's constant 192 PPQN"""
        return round((val / self.ticks) * 192)
#
#
metadata = Metas()

#
# Options: Just a place to keep these things.  Don't instantiate it.
#
class Options:
    qtime = 32      # time quantization denominator
    qvel = 0        # velocity quantization numerator
    places = 3      # places after the decimal point
    zero = False    # force all durations to '0'
    channel = 9     # 0-based MIDI channel number
    mute = False    # suppress the comment lines
    repeat = False  # repeat identical lines (don't substitute prior line's ID)

    def set(args):
        Options.qtime = args.quant_time
        Options.qvel  = args.quant_vel
        Options.places = args.places
        Options.zero = args.zero
        Options.channel = args.channel - 1  # from human 1-based to 0-based
        Options.mute = args.mute
        Options.repeat = args.repeat
#

def quantize(val, qden=32): # value, quantization denominator (def 32nd note)
    """Quantize a value to the nearest 1/qden"""
    rv = val
    if qden != 0:
        rv = round(val * qden) / qden
    return rv
#
def quantvel(val, qnum):
    """Quantize a velocity to nearest (multiple of qnum) - (qnum/2)"""
    qden = 1.0 / qnum
    shift = int(qnum / 2.0)
    return(  int( quantize(val - shift, qden) + shift ) )
#
# So we can 'cast' a raw list into an event with nicely named parts:
NoteEvent = namedtuple('NoteEvent', 'type start_time duration channel note velocity')
#
def parsenote(event, drumlist):
    global metadata
    nevent = NoteEvent( *event )
    if (Options.channel == -1) or (nevent.channel == Options.channel):  # all channels or just the one we want
        # quantize (or not) upon input, so all comparisons are to the same quantization state
        start_time  = nevent.start_time
        duration    = nevent.duration
        if Options.qtime != 0:
            start_frac  = start_time / metadata.ticks               # start_time as a fraction time/meas
            start_meas  = int(start_frac / metadata.qpermeas())     # split into integer measure number
            start_offs  = start_frac % metadata.qpermeas()          # and fraction offset into measure
            start_quant = quantize(start_offs, Options.qtime)

            start_time = (start_meas * metadata.qpermeas() + start_quant) * metadata.ticks  # rebuild the start_time w/ quantized value
            duration = quantize(duration / metadata.ticks, Options.qtime) * metadata.ticks  # same for duration (dur has no measures so its simpler)

        velocity = nevent.velocity
        if Options.qvel != 0:
            velocity = quantvel(velocity, Options.qvel)

        #'type start_time duration channel note velocity'
        newev = [ nevent.type, start_time, duration, nevent.channel, nevent.note, velocity ]
        drumlist.append(newev)
        metadata.updlast(start_time)       # update the last drum event's time
#
def parsetracks(tracks, drumlist):
    """Find drum notes and some metadata"""
    global metadata

    warn = ' '.join(  # put this long warning all on one line
        """// Warning: Multiple {0} events.
        Only using the first.
        This output may not work.""".split())
    timesigFound = False
    timesigWarned = False
    tempoFound = False
    tempoWarned = False

    for track in tracks:
        for event in track:
            etype = event[0]

            if etype == 'track_name':
                metadata.name = event[2]

            elif etype == 'time_signature':
                if timesigFound:
                    if not timesigWarned:
                        if not Options.mute:
                            print(warn.format('Time Signature'))
                        timesigWarned = True
                else:
                    metadata.timesig = TimeSig(event[2:])
                    timesigFound = True

            elif etype == 'set_tempo':
                if tempoFound:
                    if not tempoWarned:
                        if not Options.mute:
                            print(warn.format('Tempo'))
                        tempoWarned = True
                else:
                    metadata.tempo = event[2]
                    tempoFound = True

            elif etype == 'note':
                parsenote(event, drumlist)
#
def findmeas(tevents, meas):
    """Return a list of events from tevents within the given measure"""
    mlen = metadata.measlen()
    mbegin = (meas-1) * mlen
    mend   = mbegin + mlen

    # 'cast' as NoteEvents, filter by start_time, 'cast' back to score::event list-type-thing
    mevents = [ [*n] for n in [ NoteEvent(*e) for e in tevents ]
                         if (mbegin <= n.start_time < mend) ]     # the '=' in '<=' is important!
    return mevents
#
def measure2mmanotes(mevents):
    """Print all drum events in this measure formatted for MMA"""
    for n in [ NoteEvent(*e) for e in mevents ]:
        time = ((n.start_time / metadata.ticks) % metadata.qpermeas()) + 1 # first beat is 1 in human-musician lingo
        dur = 0
        if not Options.zero:
            dur  = metadata.ticks2mma(n.duration)
            if dur <= 1:   # 0 ticks and 1 ticks are both '0' with no 't' to MMA
                dur = 0
        ds = str(dur)
        if dur > 0:    # 2 or more ticks get 't' appended
            ds = ds + 't'
        print('  {0:.{3}f} {1} {2};'.format(time, ds, n.velocity, Options.places), end='')    # all on same line
    print()                                                                         # new line
#
def measures2mma(tevents, tracktag):
    """Print the MMA formatted drum measures and return a SEQUENCE list of them"""
    seq = ''                        # string for 'SEQUENCE'
    lined = {}                      # relating note lines to measure name tag { '1.000 96t 96; ...;' : 'KickDrum1M1' }
    lastmeas = metadata.lastmeas()   # we're gonna be 1-based human-centric
    for meas in range(1, lastmeas + 1):             # 1-based human-centric
        mevents = findmeas(tevents, meas)
        if len(mevents) > 0:                        # if there's something to play
            mtag = '{0}M{1}'.format(tracktag, meas) # measure's name TrackM1 etc.

            notes = io.StringIO()                   # capture this measure into 'notes'
            with contextlib.redirect_stdout(notes):
                measure2mmanotes(mevents)           # make the events (ie '1.000 96t 96;') for this measure

            nv = notes.getvalue()
            if nv in lined.keys() and not Options.repeat:   # if this measure already exists (and we are not repeating)
                mtag = lined[nv]                            # use its tag (simple 'factoring')
            else:                                   # new measure, new tag:
                print('    {0}'.format(mtag), end='')   # start the MMA line with the tag
                print(nv, end='')                       # put the events on it
                lined[nv] = mtag                    # put events and tag in the line dictionary

            seq = seq + ' {0}'.format(mtag)         # add measure's name to sequence
        else:
            seq = seq + ' z'                        # or just rest for the measure
    return( seq )
#
def tone2mma(tevents, tracktag, tonename):
    """Print the MMA text for a single drum track"""
    print('BEGIN Drum-{0}'.format(tracktag))
    print('  TONE {0}'.format(tonename))
    print('  BEGIN DEFINE')
    seq = measures2mma(tevents, tracktag)
    print('  END')
    print('  SEQUENCE ' + seq)
    print('END')
#
def header():
    """Print the TEMPO, TIMESIG, TIME, and SEQSIZE values"""
    tempo = round( (1000000.0 / metadata.tempo) * 60 )
    print('TEMPO {0}'.format(tempo))

    num = metadata.timesig.n
    den = pow( 2, metadata.timesig.d )
    print('TIMESIG {0}/{1}'.format(num,den))

    print('TIME {0}'.format(metadata.qpermeas()))

    lastmeas = metadata.lastmeas()
    print('SEQSIZE {0}'.format(lastmeas))
#
def loadscore(name=''):
    """Loads the file and returns it as a score.  What did you expect?"""
    score = None
    try:
        f = open(name, mode='rb')
    except IOError as e:
        raise
    else:
        with f:
            fb = f.read()
            score = MIDI.midi2score(fb)

    return score
#
def commentary():
    print('// MMA text produced by drumma.py')
    print('// {0}'.format(' '.join(sys.argv)))
#
def nodrums():
    oot = 'No events found on {0}'.format(
        'any MIDI Channel' if Options.channel == -1
        else 'MIDI Channel {0}'.format(Options.channel + 1) )
    print('// {0}'.format(oot))
#
def midi2mma(infile):
    """Parse the MIDI data and print the MMA text"""
    global metadata
    if not Options.mute:
        commentary()

    score = loadscore(infile)
    metadata.ticks, tracks = score[0], score[1:]

    drumlist = []       # list of ALL drum events in MIDI file
    parsetracks(tracks, drumlist)   # find drum events, learn metatadatada

    if len(drumlist) == 0:
        if not Options.mute:
            nodrums()   # complain about lack of percussion
    else:
        header()    # print MMA for some of that metadata

        dnames = getnames()
        for tonenum in range(0,128):
            tevents = [d for d in drumlist if d[4] == tonenum] # tone_events(tonenum, drumlist)
            if len(tevents) > 0:
                tracktag = dnames.get(tonenum, 'Unknown-{0}'.format(tonenum)) # either a dname or Unknown
                tonename = dnames.get(tonenum, 'ShortHiWhistle')    # unknown tone shall be ShortHiWhistle because I Am Satan!
                tone2mma(tevents, tracktag, tonename)

        # repeat enough measures of E to render it all
        print('REPEAT\n    E\nREPEATEND NOWARN {0}'.format(metadata.lastmeas()))
#
#
# https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely
@contextlib.contextmanager
def smart_open(filename=None):
    if filename and filename != '-':
        fh = open(filename, 'w')
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()
#
def intrangecheck(sval, ranje, sname=None):
    """argparse check that argument is an integer within a range"""
    if sname != None:
        sname = "for {0} ".format(sname)
    else:
        sname = ''
    try:
        ival = int(sval)
    except ValueError:
        raise argparse.ArgumentTypeError('Invalid value {0}{1} should be an integer'.format(sname, sval))

    if ival not in ranje:
        msg = "Invalid value {0}{1} not in range {2}-{3}".format(sname, ival, ranje.start, ranje.stop - 1)
        raise argparse.ArgumentTypeError(msg)
    return ival

def placescheck(sval):      return intrangecheck(sval, range(0, 13))
def quantimecheck(sval):    return intrangecheck(sval, range(0, 10001))
def quantvelcheck(sval):    return intrangecheck(sval, range(0, 128))
def chancheck(sval):        return intrangecheck(sval, range(0, 17))

def main():
    parser = argparse.ArgumentParser(
        description =  fillit("""DruMMA: Turn General MIDI drum measures into
                                 MMA-Musical MIDI Accompaniment code.
                                 Version {0}.""".format(__version__)),
        epilog = fillit(
            """Trim your MIDI to just the drum measures you want.
               Your MIDI clip should have only one tempo and only one time signature.
            """
               ),

        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('input', type=str, help='MIDI file to process')#, required=True)
    parser.add_argument('-o', '--output', type=str, help='Output file (if "-" or not set, just print the output)')
    parser.add_argument('-z', '--zero', action='store_true', help='Force all durations to "0" like BvdP does')
    parser.add_argument('-qt', '--quant_time', type=quantimecheck, default=32, metavar='DENOM',
                        help=fillit("""
                            Quantize note starts and durations
                            to the nearest 1/DENOM (4 means quarter,
                            8 means 8th, etc.).  DENOM is a positive
                            integer less than 10000,
                            default = 32 (32nd notes), 0 for no quantization"""))
    parser.add_argument('-qv', '--quant_vel', type=quantvelcheck, default=0, metavar='NUM',
                        help=fillit("""
                            Quantize velocities to the center of each NUM-width
                            velocity step (if NUM=4, centers are 2,6,10, etc.).
                            NUM is a positive integer less than 128,
                            default = 0 = no quantization"""))
    parser.add_argument('-p', '--places', type=placescheck, default=3, help='Number of places (between 0 and 12) to include after the decimal point (default 3)')
    parser.add_argument('-c', '--channel', type=chancheck, default=10, help='MIDI Channel to find drum events on (0=all, default=10)')
    parser.add_argument('-m', '--mute', action='store_true', help='Suppress commentary lines')
    parser.add_argument('-r', '--repeat', action='store_true', help='Repeat identical lines (don\'t factor)')

    # move the 'input' to the front and name it input.mid
    spusage = parser.format_usage().split()
    parser.usage  = ' '.join([ spusage[1], 'input.mid', *spusage[2:-1]  ])

    args = parser.parse_args()
    Options.set(args)

    with smart_open(args.output) as ofile:
        try:
            with contextlib.redirect_stdout(ofile):
                midi2mma(args.input)
        except BrokenPipeError:
            pass               # ignore the pipe broken by quitting 'more'
#

if __name__ == '__main__':
    main()
