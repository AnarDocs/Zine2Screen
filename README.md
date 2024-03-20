# Zine2Screen
Convert Zine to One Page PDF

Want to read a zine on your screen - but the pages are not in order?

Convert Imposed PDFs (Zine Booklet) to Pagnated PDF & Images

Usage:
```
chmod +x zine2screen.sh
./zine2screen zine.pdf <- output to zine_output
./zine2screen zine.pdf zinescreen <- output to zinescreen
./zine2screen -r300 zine.pdf <- 300 dpi
# (300 for print / default is 150 / 75 is quick and usually fine for screen)
```

Page images are outputed to ./zine_output/images

They can be converted to jpg with -
`mogrify -format jpg *.png`

To use this script on Linux, MacOS or Windows (WSL)

Run the `dependencies.sh` script, or ...

* Debian / Ubuntu - sudo apt install -y poppler-utils imagemagick
* Redhat / Fedora - sudo yum install -y poppler-utils ImageMagick
* MacOs - brew install poppler imagemagick

Some Zine resources ...
