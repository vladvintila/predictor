# Predictor exercise

Read market data and predict the next three data points for each ticker.

The data is read from .csv files located in local directories which names
represent the respective stock exchange name. From each .csv there are
extracted ten consecutive data points from a randomly chosen starting point.


## Prerequisites

Python 3.8 or newer.

## How to run

Input folders are expected to be in the current working directory.

```
python3.12 predictor.py --files-per-exchange 2
```

Output .csv files are created under the `predictions` folder, each under their
respective stock exchange named folder.

There are a few options documented under the `-h` flag:

```
python3.12 predictor.py -h

options:
  -h, --help            show this help message and exit
  --files-per-exchange {1,2}
                        REQUIRED. Recommended number of files to read for each exchange.
  --data-sanity-check {file,sequence,none}
                        Check if data has the correct structure(stock-id.dd-mm-YYYY.stock-value):
                            file - check the entire .csv file
                            sequence - only check the ten data points
                            none - disable data check - most efficient.
                        If a file or set of data is not in the correct format it won't be processed
  --disable-auto-discover
                        Set to disable auto-discovery of directories containing .csv files in the current working directory
  --directories DIRS [DIRS ...]
                        Ignored by default. Used in case --disable-auto-discovery is set.
                        List of directories to look into for .csv files.
```

One more example:
```
python3.12 predictor.py --files-per-exchange 2 --disable-auto-discover --directories NASDAQ
```


## Comments

I prioritized the human experience and spent some time refining the arguments
and their explanations and code comments. Besides striving to meet the task
requirements I added data validations and tried to have generic code rather
then specific to the constraints of the task.

There are a lot of improvements I would make given more time:
 - I would write unit tests. I tried to structure the code to be friendly for
 that.
 - I would improve the data sanity checking function as it's a bit bare-bones,
 and more things would need to be checked. For example:
   - alignment of ticker name and file name, consistency of ticker name in a
file
   - checking if the records are in the correct order
   - a regex check on the stock name field.
 - I was thinking I could make a docker container to be more portable, but it
 seems kind of off-topic.
 - The predictor algorithm is implemented only for the 3 predicted points, as
 opposed to something for n points. The given algorithm doesn't look like it
 should be applied to more points, though.

