#!/usr/bin/tclsh

set file [lindex $argv 0]

if {$file == ""} {
    set fp stdin
} else {
    set fp [open $file r]
}

puts "\\documentclass\[pdf,allen\]{prosper}"
#puts "\\usepackage\[dvips\]{color}"
puts "\\usepackage{graphicx,url}"

puts "\n\\title\{Changepoint detection in network measurements}"
puts "\\author\{Allen B. Downey\}"
puts "\\institution\{Franklin W. Olin College of Engineering\}"

puts "\\begin{document}"
puts "\\maketitle"


set pattern "includegraphics\[.*\]\{(.*)\}"
set pattern "includegraphics.*{(.*)}"

while {[gets $fp line] != -1} {
    if {[regexp $pattern $line match name]} {
	
	puts "\n\n\\begin{slide}{title}"

	puts "\n\\raisebox{-2.5in}{"
	puts "\\includegraphics\[width=3.0in,height=2.5in\]{$name}"
	puts "}"
	puts "\\nolinebreak"
	puts "\\begin{minipage}\[t\]{1.8in}"
	
	puts "\n\\begin{itemize}"
	
	puts "\n\\item ."

	puts "\n\\end{itemize}"
	
	puts "\n\\end{minipage}"
	puts "\\end{slide}"

    } else {
	#puts stderr "Bad line: $line"
    }
}

puts "\n\\end{document}"
