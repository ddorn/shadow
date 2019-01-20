# Experimenting with shadows

### Install

Discaimer: this was tested on python 3.7, and should work on 3.6 with `dataclasses` installed, but it wont before.

Alright, let's install it. I use `visibility` to cast the shadow, but to install it
you need to get `pybindgen` first, and it somehow doesn't automatically install.

	pip install pybindgen

To get the rest of the requirements:

	git clone https://gitlab.com/ddorn/shadow/
	cd shadow
	pip install -r requirements.txt

### Use it

To start it just run

	python .

It should lag a little at the begining, because I do heavy calculation to get a "realistic" mask
(aka not a circle), but once it's cached, it should go all right.

Bindings :
 - [Esq] Quit
 - [l]   Re-generate lights
 - [s]   Toggle shadows
 - [p]   Screenshot
 - [m]   Player follow mouse
 - [d]   Toggle debug mode


And the map editor :

	python apple.py

Note that there is only one level, and if you save it it will replace the current.


### In the end

It doesn't relly matter, but you can do cool shadows with pygame and numpy. It actually runs at about 80-90 fps
on my machine, but with more optimisation, there could be enough proccessing left for the rest of the game.

Have fun !
Diego
