from sys import version_info, exit
from time import strftime
from subprocess import Popen, PIPE, run

static_parameters = {
    # scanimage settings
    '--format': 'tiff',
    '--device-name': 'coolscan3:scsi:/dev/sg3',

    # scanner settings to use for color film
    #'--negative': 'yes', # doesn't work for black and white
    #'--infrared': 'yes', # use ICE for color film
    #'--ae-wb': 'yes', # use white balance in addition to AE for color film

    # scanner settings to use for black and white film
    '--ae': 'yes',

    # scanner settings to use for all film
    '--autofocus': 'yes',

    # scanner settings to use for previews
    #'--preview': 'yes',
    #'--resolution': '84'

    # scanner settings to use for final copies
    #'--resolution': '2700', # 2700 is the default setting
    '--depth': '12'
}

prompts = [
    'First, insert the film strip and verify that you see a steady green light.\n\nWhen the scanner is initialized, follow the prompts to enter information about the film strip you are scanning. Type quit at any prompt to quit.\n\nEnter the number of rolls you have scanned today. Files are named using a date, such as 2018_01_31, a serial number for rolls scanned today starting at 00, a film prefix, such as 400TX, and a frame number.\n\nRoll serial number: ',
    'Film prefix: ',
    'Enter frame numbers you are scanning in ascending order, such as 0-6, 3, 8-8. If you don\'t enter an ending frame, the program scans six frames. To scan one frame, enter n-n. If you are scanning frame 00, enter 0-n, and manually rename the files.\n\nFrame numbers: '
]

def get_input(text):
    print('\n')

    # show an input prompt
    data = input(text)

    if data == 'quit':
        exit()
    else:
        # limit input string to 25 characters--we're creating file names here
        return data[:25]

def create_file_name(elements):
    # add today's date, the first element
    elements.insert(0, strftime('%Y%d%m'))

    # add a leading zero to make a two-digit serial (for dumb file sorting)
    elements[1] = elements[1].zfill(2)

    # add the batch page number and file extension, the last element
    elements.append('%d.TIFF')

    # create and return a file name string
    s = '_'.join(elements)

    return s

def parse_scanner_parameters(user_list):

    # start with the static parameters configured at the top of the file
    params = static_parameters

    # parse the batch parameter, which determines file name format
    file_name = create_file_name(user_list[0:2])

    # parse the frame-count and batch-start parameters
    strings = user_list[2].split("-", 1)

    # check whether there is an ending frame
    if len(strings) == 1:
        # if no ending frame, assume a strip of six frames
        n = "6"
    else:
        # otherwise, calculate the number of frames
        n = str(
            int(strings[1]) - int(strings[0]) + 1
        )

    params.update(
        {
            '--batch': file_name,
            '--batch-start': strings[0],
            '--batch-count': n
        }
    )

    return params

def build_command_args(params):
    # building this command:
    # scanimage -p --format=tiff -d coolscan3:scsi:/dev/sg3 --batch=format%d.tiff --batch-start=first_frame --frame-count num_frames
    args = ['scanimage', '-p']

    for key, value in params.items():
        args.append(key + '=' + value)

    return args

def test_scanner_media():
    # args to pass to run() to run the help for our device
    help_command = ['scanimage', '--help', '--device-name', static_parameters['--device-name']]

    # with the coolscan3 driver, if this text is in the output of the help command,
    # it means the film isn't loaded successfully
    bad_string = 'frame 1..0 (in steps of 1) [inactive]'

    # I am not exactly sure how this works, we pipe the output, set universal_newlines to true so it's a string,
    # and read each line to see if it has our bad string.
    with Popen(help_command, stdout=PIPE, universal_newlines=True) as process:
        for line in process.stdout:
            if bad_string in line:
                # if we find the film isn't loaded, return False
                return False

    # otherwise, return True
    return True

def reset_scanner():
    reset_command = ['scanimage', '--reset', '--device-name', static_parameters['--device-name']]
    run(reset_command)

while(1):
    # exit if this is Python 2 or earlier because input() is spooky in Python 2
    if not version_info[0] > 2:
        print('application requires python 3 or later')
        exit()

    # define the user parameters list
    user_parameters = []

    for i, line in enumerate(prompts):
        # reset everything when we're done looping over the prompts
        if i == 0:
            user_parameters = []

        param = ''

        # don't proceed until the user enters something at the prompt
        while param is '':
            param = get_input(line)

        user_parameters.append(param)

    # check if the film is loaded successfully
    if test_scanner_media() is True:
        # if so, build the command and run it
        all_params = parse_scanner_parameters(user_parameters)

        # Debug: to see the command that will be run, uncomment this line.
        #print(build_command_args(all_params))

        run(build_command_args(all_params))
    else:
        # if not, print an error and let the user try again
        reset = get_input("Film isn't loaded successfully. Enter r to reset the scanner press Enter to try again.\n\nReset? ")
        if reset == 'r': reset_scanner()
