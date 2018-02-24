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
    'Enter frame numbers you are scanning in ascending or descending order, such as 0-6, 3, 36-30, or 1-1. If you are scanning frame 00, enter 0-n, and manually rename the files.\n\nFrame numbers: '
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

def create_file_names(user_list):
    file_names = []

    # get the first frame and the last frame
    endpoints = user_list[2].split("-", 1)
    endpoints = list(map(int, endpoints))

    # if the frames are backwards, like 6-1, then make the endpoints negative so we get a positive range
    # we will use the absolute value to discard negative signs in the frame numbers below.
    if len(range(endpoints[0], endpoints[1])) is 0:
        endpoints = [-x for x in endpoints[0:2]]

    # if they enter 1, assume they mean 1-1. the parsing logic depends on having two endpoints
    if len(endpoints) is 1:
        endpoints.append(endpoints[0])

    user_list.insert(0, strftime('%Y%d%m'))

    # add a leading zero to make a two-digit serial (for dumb file sorting)
    user_list[1] = user_list[1].zfill(2)

    # put together a string out of the user inputs, but leave out the range (i.e. 1-6, the last element in the list)
    name_template = '_'.join(user_list[0:3])

    for i in range(endpoints[0], endpoints[1]+1):

        # add the frame number with a leading 0
        # use the absolute value of the frame number in case we made them negative above
        s = name_template + '_' + str(abs(i)).zfill(2)

        # add the file extension
        s = s + '.' + static_parameters['--format'].upper()

        # add each file name to the list of file names
        file_names.append(s)


    return file_names


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

    # define the file_names list
    file_names = []

    for i, line in enumerate(prompts):
        # reset everything when we're done looping over the prompts
        if i == 0:
            user_parameters = []

        param = ''

        # don't proceed until the user enters something at the prompt
        while param is '':
            param = get_input(line)

        user_parameters.append(param)

    # TO DO: uncomment the media checking part [
    # check if the film is loaded successfully
    if test_scanner_media() is True:
        # if so, build a list of filenames and run a series of commands

        file_names = create_file_names(user_parameters)
        print(file_names)

        for i, v in enumerate(file_names):
            all_params = static_parameters

            # add the scanner page number, starting at 1
            all_params.update(
                {
                    '--frame': str(i+1)
                }
            )

            # build and run a command to scan.
            # send the output to a file open in write mode with the name we built.
            print('Scanning ' + v)
            run(build_command_args(all_params), stdout=open(v, 'w'))

    else:
        # if not, print an error and let the user try again
        reset = get_input("Film isn't loaded successfully. Enter r to reset the scanner press Enter to try again.\n\nReset? ")
        if reset == 'r': reset_scanner()
