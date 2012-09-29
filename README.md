# TUT restaurant's food info in JSON

This project's main goal is to offer an easy way to get food data from Tampere University of Technology.

I hope someone could build an web app (html5 etc.) or mobile app with help of this interface.

If not, I'll do it myself :D

I'm not going to promise full uptime for the interface, but the data can be fetched from [relativity.fi](http://relativity.fi/juvenes/index.html)
(Currently only in Finnish, documentation can be found there too)

Since the code is open source, feel free to contribute or use it for your own purposes as long as licence conditions are met.

## Usage

Script creates by default food.json or ruoka.json file, depending on language.
See the source and class initializer for example file path modification purposes etc.

To run:
`python json_food_TUT.py <language>`

Language: fi or en, defaults to fi if no parameter given
I recommend to use cron for scheluded runs.

## License

Copyright (C) 2012 Olli-Pekka Heinisuo

Distributed under the [Apache-2.0 license](http://www.apache.org/licenses/LICENSE-2.0.html)