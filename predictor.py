import argparse
import csv
import os
import random
import sys
import warnings

from datetime import datetime, timedelta


def parse_arguments(args):
    parser = argparse.ArgumentParser(
        description='Read market data and predict the next three data '
        'points for each ticker.\n'
        '\n'
        'The data is read from .csv files located in directories which '
        'names represent the respective stock exchange name.\nFrom each '
        '.csv there are extracted ten consecutive data points from a '
        'randomly chosen starting point.',
        # Custom formatter needed to enable new lines in argument descriptions.
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--files-per-exchange', type=int, choices=[1, 2],
                        help='REQUIRED. Recommended number of files to read '
                        'for each exchange. ', required=True,
                        dest='files_number')

    parser.add_argument('--data-sanity-check', choices=['file', 'sequence',
                        'none'], default='file', help='Check if data has the '
                        'correct structure(stock-id.dd-mm-YYYY.stock-value):\n'
                        '    file - check the entire .csv file\n'
                        '    sequence - only check the ten data '
                        'points\n'
                        '    none - disable data check - most efficient.\n'
                        'If a file or set of data is not in the correct format'
                        ' it won\'t be processed',
                        dest='data_check')

    parser.add_argument('--disable-auto-discover',
                        action='store_true', help='Set to disable '
                        'auto-discovery of directories containing .csv files '
                        'in the current working directory',
                        dest='no_dir_search')

    parser.add_argument('--directories', nargs='+',
                        help='Ignored by default. Used in case '
                        '--disable-auto-discovery is set.\n'
                        'List of directories to look into for .csv files.',
                        dest='dirs')

    return parser.parse_args(args)


def get_files(dirs, files_number):
    """
    Get .csv files from a list of directories. Expects an additional file
    number limit argument. It is useful to save the directory where they came
    from for creating the output directories.
    """
    files = []
    for dir in dirs:
        file_count = 0
        for file in os.listdir(dir):
            # Don't go over the imposed file limit. While the limit is defined
            # to be either 1 or 2, the code supports setting any limit.
            if file_count >= files_number:
                continue
            if file.endswith('.csv'):
                file_count += 1  # Count only .csv files
                file_path = os.path.join(dir, file)
                files.append(file_path)
        if file_count < files_number:
            warnings.warn('Found only {} .csv files in directory {} but the '
                          'recommended number to read from is {}.'
                          .format(file_count, dir, files_number))

    return files


def check_data_sanity(rows):
    """
    Reads a list of lists and tests that each individual list is in format
    "STRING,DD-MM-YYYY,2-decimal float". It also checks if the main list should
    never have less than 10 items.
    """
    if len(rows) < 10:
        return False

    for row in rows:
        if not row[0].isalpha():
            return False
        try:
            if row[1] != datetime.strptime(row[1],
                                           '%d-%m-%Y').strftime('%d-%m-%Y'):
                raise ValueError
        except ValueError:
            return False
        try:
            if row[2] != '{:.2f}'.format(float(row[2])):
                raise ValueError
        except ValueError:
            return False
    return True


def extract_values(file, data_check):
    """
    Get a .csv file and extract 10 consecutive rows from a random starting
    point. Checks if the file or sequence of 10 has the correct format. This
    is controlled by the --data-sanity-check option.
    Returns a list of 10 rows if the format is correct or False if not.
    """
    with open(file) as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)

    if data_check == 'file':
        if not check_data_sanity(rows):
            warnings.warn('File {} has corrupted data.'.format(file))
            return False

    # Get a random number but make sure we have at least 10 rows to spare.
    try:
        random_index = random.randint(0, (len(rows) - 10))
    except ValueError:
        # We should not get here if the file was checked for correct data.
        warnings.warn('File {} has corrupted data. Consider checking the file '
                      'for data sanity'.format(file))
        return False
    ten_values = []
    for i in range(10):
        # Start from the random position and save the next 10 rows.
        ten_values.append(rows[random_index + i])

    if data_check == 'sequence':
        if not check_data_sanity(ten_values):
            warnings.warn('File {} has corrupted data.'.format(file))
            return False

    return ten_values


def predict_values(values):
    """
    Gets a list of 10 rows with and returns the next 3 predictions according
    to the given algorithm, in the same format.
    """
    highest = 0  # I assume these can't have negative prices.

    # Get the highest value.
    for value in values:
        price = float(value[2])  # Convert from string.
        if price > highest:
            highest = price

    second_highest = 0
    # Get the second highest value.
    for value in values:
        price = float(value[2])  # Convert from string.
        # There could be multiple lines with the highest value, so we skip
        # all of them.
        if price > second_highest and price != highest:
            second_highest = price

    if second_highest == 0:
        # Either all values are 0 or all values are the max value. It means
        # we cannot obtain a 2nd highest value.
        raise ValueError('Cannot obtain second highest value! Check input '
                         'files')

    first_prediction = second_highest

    # I assume "n+2 data point has half the difference between n and n+1"
    # actually means n+2 is the average of n and n+1, as that makes sense. What
    # this sentence is telling me is that n+2 is abs(n - n+1).
    second_prediction = (float(values[-1][2]) + first_prediction) / 2

    # I assume "n+3 data point has 1/4th the difference between n+1 and n+2"
    # means n+3 is bigger(or smaller) than n+2 by a quarter of the absolute
    # difference between n+1 and n+2. This is not what the requirement says
    # though. I would have clarified these requirements as it's not clear.
    if second_prediction >= first_prediction:
        third_prediction = (second_prediction +
                            (second_prediction - first_prediction) / 4)
    else:
        third_prediction = (second_prediction +
                            (first_prediction - second_prediction) / 4)

    # Convert back to the expected format.
    predictions = ['{:.2f}'.format(first_prediction),
                   '{:.2f}'.format(second_prediction),
                   '{:.2f}'.format(third_prediction)]

    # Get the last item's date
    date = datetime.strptime(values[-1][1], '%d-%m-%Y')
    predicted_rows = []
    for index in range(3):
        row = []
        row.append(values[0][0])  # Ticker is the same.

        # Many date exemptions and edge-cases solved by timedelta.
        date += timedelta(days=1)
        row.append(date.strftime('%d-%m-%Y'))

        row.append(predictions[index])
        predicted_rows.append(row)

    return predicted_rows


def main(args):
    parsed_args = parse_arguments(args)

    if parsed_args.no_dir_search:
        dirs = parsed_args.dirs
    else:
        # All directories in current working directory.
        dirs = filter(os.path.isdir, os.listdir(os.getcwd()))

    files = get_files(dirs, parsed_args.files_number)

    for file in files:
        values = extract_values(file, parsed_args.data_check)
        if values:  # it passed the data sanity
            predicted_values = predict_values(values)
            final_values = values + predicted_values

            output_file_path = 'predictions/{}'.format(file)
            # Make a 'predictions' folder contains the same structure as the
            # input folders.
            os.makedirs(os.path.split(output_file_path)[0], exist_ok=True)

            with open(output_file_path, 'w') as output_csv_file:
                csv_writer = csv.writer(output_csv_file)
                csv_writer.writerows(final_values)

    # write_file(extracted_values, predicted_values)


if __name__ == '__main__':
    main(sys.argv[1:])  # Pass arguments only.
