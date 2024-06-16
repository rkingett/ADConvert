# ADLib - Audio Description Script Library Processing Thingy
# by Brett Coulstock
# Public Domain. Do what thou wilt!

from dataclasses import dataclass, field
from datetime import *
import re
import csv
import tomli

import json
#import sys
#import datetime
#import glob

"""

== To Do ==

- netflix output format
- html recording script
- joining
- splitting
- direction free output (strip FAST, Prn, Act, >)
- Combine features into a single command with arguments

== Bugs ==
- Mypy doesn't allow metadata to be optional None. Fix.
- Kyle needs to have 2 grades of "fast". One underline, one bold underline. Formalise [FAST] and [VFAST].

=== FIXED ===
- Any place "event.voice_over = event.voice_over" is problematic. Fix.
- webvtt export permenantly transforms > into &gt; - needs to only operate on a copy for that.
- RTF output seems to be without capital letters for first sentence!


== Function List ==

=== Input ===
parse_srt(lines:list[str]) -> list[AdEvent]

=== Helper ===
get_duration(a:str, b:str) -> str
find_fast(voiceover) -> bool

=== Output ===
write_srt(output_filename:str, ad_script:list[AdEvent], start_from:int = 1)
write_csv(output_filename:str, ad_script:list[AdEvent], collapse_lines:bool = False, start_from:int = 1)
write_kyle(output_filename:str, ad_script:list[AdEvent], numbered:bool = False)
write_rtf(output_filename:str, ad_script:list[AdEvent], metadata:dict)
write_webvtt(output_filename:str, ad_script:list[AdEvent], metadata:dict, start_from:int = 1, collapse_lines:bool = False)

"""


@dataclass
class AdEvent:

	""" Class for encapsulating a record of a single Audio description event or cue """

	number: int = 0
	time_in: str = ""
	time_out: str = ""
	duration: str = "" 
	cue: str = ""
	direction: list = field(default_factory=list) 
	voice_over: str = ""

@dataclass
class AdMetaData:

	""" Class for encapsulating and formatting a record of metadata """

	title: str = ""
	author: str = ""
	subject: str = ""
	keywords: str = ""
	company: str = ""
	date: str = ""
	licence: str = ""
	rights: str = ""
	url: str = ""
	filename: str = ""

	def load_metadata(self, input_filename:str):

		# We're now using TOML. Much nicer.
		try:
			with open(input_filename, "rb") as read_file:
				data = tomli.load(read_file)
		except:
			print("Unable to open file " + input_filename)
			exit()

		self.title = data["title"]
		self.author = data["author"]
		self.date = data["date"].strftime("%Y-%m-%d")
		self.licence = data["licence"]
		self.rights = data["rights"]
		self.url = data["url"]
		self.subject = data["subject"]
		self.keywords = data["keywords"]
		self.company = self.author
		self.filename = data["filename"] 


	def get_markdown_metadata(self) -> str:

		infoblock:list[str] = []

		# YAML style, works on Pandoc
		infoblock.append("---")
		infoblock.append("title: " + self.title)
		infoblock.append("author: " + self.author)
		infoblock.append("description: " + self.subject)
		infoblock.append("keywords: [ " + self.keywords + " ]")
		infoblock.append("date: " + self.date)
		infoblock.append("---\n")
		infoblock.append("# " + self.title + "\n")

		return '\n'.join(infoblock)


	def get_html_metadata(self) -> str:
		
		infoblock:list[str] = []

		infoblock.append("<title>" + self.title + "</title>")
		infoblock.append("<meta name=\"author\" content=\"" + self.author + "\">")
		infoblock.append("<meta name=\"description\" content=\"" + self.subject+ "\">")
		infoblock.append("<meta name=\"keywords\" content=\"" + self.keywords + "\">")

		return '\n'.join(infoblock)


	def get_webvtt_info_block(self) -> str:

		""" Format metadata for inclusion in webvtt file """

		infoblock:list[str] = []

		infoblock.append("NOTE")
		infoblock.append("Title: " + self.title)
		infoblock.append("Author: " + self.author)
		infoblock.append("Date: " + self.date)
		infoblock.append("Subject: " + self.subject)
		infoblock.append("Copyright: " + self.rights)
		infoblock.append("Licence: " + self.licence)
		infoblock.append("URL: " + self.url)

		return '\n'.join(infoblock)


	def get_rtf_info_block(self) -> str:

		"""
			Format metadata for inclusion in RTF file \\i\\info block.
			I do not believe subject and keywords are part of the spec, but libre-office
			and abi-word accept both fields.

			Use the document comment \\doccomm field for copyright and URL info.
		"""

		infoblock:list[str] = []

		infoblock.append("{\\info\n")
		infoblock.append("{\\title " + self.title + "}\n")
		infoblock.append("{\\author " + self.author + "}\n")
		infoblock.append("{\\subject " + self.subject + "}\n")
		infoblock.append("{\\keywords " + self.keywords + "}\n")
		infoblock.append("{\\company " + self.author + "}\n")
		infoblock.append(self.get_rtf_date())
		infoblock.append("{\\doccomm Copyright: " + self.rights
			+ "\n" + ";  Licence: " + self.licence 
			+ "\n" + ";  URL: " + self.url
			+ "}\n")
		infoblock.append("}")

		return ''.join(infoblock)


	def get_rtf_date(self) -> str:

		""" Format for RTF date is : {\\creatim\\yr2023\\mo08\\dy18} """
		
		x:list[str]  = self.date.split("-")

		if len(x) != 3:
			raise ValueError('Metadata date format incorrect. Must be yyyy-mm-dd.')
		
		return "{\\creatim\\yr" + x[0] + "\\mo" + x[1] + "\\dy" + x[2] + "}\n"



def parse_csv(lines:list[str]) -> list[AdEvent]:

	"""
	Convert a CSV file into internal format, defined as a dataclass
	"""

	for line in lines:
		line = line.strip()
		fields = ','



def parse_srt(lines:list[str]) -> list[AdEvent]:

	"""
	Convert an SRT file into internal format, defined as a dataclass
	"""

	cues = []

	GET_TEXT = 1
	WAITING = 2
	cue = 0	
	current_state = WAITING
	start_time:str = ""
	end_time:str = ""
	text:str = ""
	duration:str = ""
	text_line:int = 0

	current_cue = AdEvent()

	for line in lines:
		line = line.strip()

		if "-->" in line:
			cue += 1
			start_time = line[0:12]
			end_time = line[17:]
			duration = get_duration(start_time,end_time)
			current_state = GET_TEXT
			text_line = 0

			current_cue.number = cue
			current_cue.time_in = start_time
			current_cue.time_out = end_time
			current_cue.duration = duration

			continue

		if line == "":
			current_cue.voice_over = text

			# Check text for directions (eg: [FAST])
			x = re.findall("(\[[^]]*\])",text,re.MULTILINE)
			if x != None:
				current_cue.direction = x # An array of 1 or more elements

			cues.append(current_cue)

			# Reset everything
			current_cue = AdEvent() 
			text = ""
			current_state = WAITING
			continue

		if current_state == GET_TEXT:
			if text_line == 0:
				text += line
				text_line += 1
			else:
				text += "\n" + line

	if current_state == GET_TEXT:
		current_cue.voice_over = text
		cues.append(current_cue)

	return cues



# =======================================

#	Helper functions

# =======================================

def get_duration(a:str, b:str) -> str:

	"""
	Calculate the duration of two times.
	Doesn't check if time a is less than time b at the moment.
	"""

	start = datetime.strptime(a, "%H:%M:%S,%f")
	end = datetime.strptime(b, "%H:%M:%S,%f")

	duration = str(end - start)

	try:
		# If it fails this, it's in the wrong format
		# Nb: check. Updates to code may mean that this never fails
		#     and therefore may be redundant
		test = datetime.strptime(duration,"%H:%M:%S,%f")
	except:
		# This will make it the right format
		duration = "0" + duration
		if len(duration) <= 8:
			duration += ".000000"

	return(str(duration))


def add_to_time(time:str, offset:int) -> str:

	"""
	Take a time and add offset seconds to it.
	"""

	start = datetime.strptime(time, "%H:%M:%S,%f")
	new_time = start + timedelta(0,offset)

	return(new_time.strftime("%H:%M:%S,%f"))


def find_fast(voiceover) -> bool:

	found = False
	for i in voiceover:
		if "[FAST" in i or "[fast" in i:
			found = True
	return found


def convert_to_utf(voiceover) -> str:

	# Smart Double Quotes ... someday
	#voiceover = voiceover.replace("“","\\'93") # Convert Unicode double quotes
	#voiceover = voiceover.replace("”","\\'94") # Convert Unicode double quotes

	# Smart Single Quotes ... someday
	#voiceover = voiceover.replace("‘","\\'91") # Convert Unicode single quotes - left
	#voiceover = voiceover.replace("’","\\'92") # Convert Unicode single quotes - right

	voiceover = voiceover.replace("--","—") # Replace unicode Em dash with real thing
	voiceover = voiceover.replace("...", "…") # Replace unicode ellipsis with real thing


	return voiceover


# =======================================

#	Output functions

# =======================================

def write_srt(output_filename:str, ad_script:list[AdEvent], start_from:int = 1):

	"""
	Convert internal format to a .srt file
	"""

	srt_content:list[str] = []
	count:int = start_from

	for event in ad_script:
		try:
			srt_content.append(str(count) + '\n')
			count += 1
			srt_content.append(event.time_in + " --> " + event.time_out + '\n')
			srt_content.append(event.voice_over + '\n\n')
		except:
			print("Problem at: ")
			print(event)
	
	# Remove any trailing newlines from the last event
	x:str = srt_content.pop().strip()
	srt_content.append(x)

	with open(output_filename, "w") as output_file:
		for line in srt_content:
			output_file.write(line)



def write_csv(output_filename:str, ad_script:list[AdEvent], collapse_lines:bool = False, start_from:int = 1):

	""" Render the internal data structure into tab delimited CSV data """

	with open(output_filename, mode='w') as ad_file:
		ad_writer = csv.writer(ad_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		count:int = start_from

		for event in ad_script:

			voiceover = event.voice_over 
			if collapse_lines:
				voiceover = voiceover.replace('\n',' ')

			ad_writer.writerow([
				count, 
				event.time_in,
				event.time_out,
				event.duration[:-3], # Truncate least significant 3 digits.
				voiceover
			])

			count += 1


def write_kyle(output_filename:str, ad_script:list[AdEvent], metadata:AdMetaData = None, numbered:bool = False, collapse_lines:bool = False):

	# Create the RTF content

	rtf_content = []

	# ... Header

	# Nb: US english is 1033, UK english is 2057 
	# Turn on widow/orphan control. \windowctrl

	rtf_content.append("""{\\rtf1\\ansi\\deflang2057\\widowctrl\\deff0 {\\fonttbl {\\f0 Helvetica;}{\\f1 Times;}}

{\colortbl
;
\\red128\\green128\\blue128;
\\red255\\green0\\blue0;
}

""")

	# ... Info Block (Metadata)

	if metadata is not None:
		rtf_content.append(metadata.get_rtf_info_block())
		rtf_content.append('\n')

		# ... Page Header
		rtf_content.append("{\\header \\pard\n" + metadata.title + " by " + metadata.author + "\n")
		rtf_content.append("\tPage: \\chpgn\n\\par}\n\n")

		# ... Title
		rtf_content.append("{\\pard\n\\qc\\b\\f3\\fs40" + metadata.title + "\n\\par}")
		rtf_content.append("{\\pard\\par\\qc " + metadata.author + "\\par}")
	else:
		rtf_content.append("{\\header \tPage: \\chpgn\n\\par}\n\n")

	# Add the events

	count = 1
	lines = 0

	font_size = "\\fs36"

	for event in ad_script:

		voiceover = event.voice_over

		# In theory, this creates an invisible "comment"
		# However, it doesn't survive being opened in another program and saved.
		# rtf_content.append("\n{\\*\\time_in\n" + event.time_in + "\n}")

		start = "\n\\par\\par\n" + font_size + " "
		end = ""

		# For events marked [FAST], bold and underline them
		if event.direction != None:

			if find_fast(event.direction):
				# Fast-ish: underline, Fast: bold+underline
				if "ish" in event.direction[0] or "ISH" in event.direction[0]:
					start += "{\\ul "
				else:
					start += "{\\b\\ul "

				end = "}"
				x = re.match("(\[[^]]*\])",voiceover)
				if x != None:
					# Note, mypy has no way of knowing that x is not None
					# but with the above conditional, we guarantee it.
					# so typechecking of x ignored here.
					voiceover = voiceover[x.span()[1]:].strip() # type:ignore


		# Fix some character conventions. A bit on the brute-force side. :-/

		voiceover = voiceover.replace("{","\\'7b") # Convert Curly Braces
		voiceover = voiceover.replace("}","\\'7d") # Convert Curly Braces 

		voiceover = voiceover.replace("“","\\'93") # Convert Unicode double quotes
		voiceover = voiceover.replace("”","\\'94") # Convert Unicode double quotes

		voiceover = voiceover.replace("‘","\\'91") # Convert Unicode single quotes - left
		voiceover = voiceover.replace("’","\\'92") # Convert Unicode single quotes - right

		voiceover = voiceover.replace("--","\\'97") # Replace psuedo Em dash
		voiceover = voiceover.replace("—","\\'97") # Replace unicode Em dash

		voiceover = voiceover.replace("...","\\'85") # Replace psuedo ellipsis with real thing
		voiceover = voiceover.replace("…","\\'85") # Replace unicode ellipsis with real thing

		# Collapse lines = honour carriage returns as line breaks.
		if collapse_lines:
			voiceover = voiceover.replace('\n',' ')
		else:
			voiceover = voiceover.replace('\n','\\par\n')

		if numbered:
			rtf_content.append(start + str(count) + ".  " + voiceover + end)
		else:
			rtf_content.append(start + voiceover + end)

		count += 1

	# ... Close the RTF document
	rtf_content.append("\n}")

	# Save the RTF document
	with open(output_filename, "w") as rtf_file:
		for i in rtf_content:
			rtf_file.write(i)


def write_rtf(output_filename:str, ad_script:list[AdEvent], metadata:AdMetaData = None, collapse_lines:bool = False):

	"""

	Issues:

	- Cues can go over page. Any fix?
		- We say only so many cues per page
		- We can try and count lines, estimate, could go wrong

	"""

	# Create the RTF content

	rtf_content = []

	# ... Header

	# Nb: US english is 1033, UK english is 2057 
	# Turn on widow/orphan control. \windowctrl

	rtf_content.append("""{\\rtf1\\ansi\\deflang2057\\widowctrl\\deff0 {\\fonttbl {\\f0 Courier;}{\\f1 Times;}}

{\\colortbl
;
\\red128\\green128\\blue128;
\\red255\\green0\\blue0;
}

""")

	# ... Info Block (Metadata)

	if metadata is not None:
		rtf_content.append(metadata.get_rtf_info_block())
		rtf_content.append('\n')

		# ... Page Header
		rtf_content.append("{\\header \\pard\n" + metadata.title + "\n") # + " by " + metadata.author + "\n")
		rtf_content.append("\t\t\tPage: \\chpgn\n\\par}\n\n")

		# ... Title
		rtf_content.append("{\\pard\n\\qc\\b\\f3\\fs40" + metadata.title + "\n\\par}")
		rtf_content.append("{\\pard\\par\\qc " + metadata.author + "\\par}")
	else:
		rtf_content.append("{\\header \tPage: \\chpgn\n\\par}\n\n")

	# Add the events

	count = 1
	lines = 0

	for event in ad_script:

		rtf_content.append("\n\\par\\par\n")

		voiceover = event.voice_over


		# Fix some character conventions. A bit on the brute-force side. :-/

		voiceover = voiceover.replace("“","\\'93") # Convert Unicode double quotes
		voiceover = voiceover.replace("”","\\'94") # Convert Unicode double quotes

		voiceover = voiceover.replace("‘","\\'91") # Convert Unicode single quotes - left
		voiceover = voiceover.replace("’","\\'92") # Convert Unicode single quotes - right

		voiceover = voiceover.replace("--","\\'97") # Replace psuedo Em dash
		voiceover = voiceover.replace("—","\\'97") # Replace unicode Em dash

		voiceover = voiceover.replace("...","\\'85") # Replace psuedo ellipsis with real thing
		voiceover = voiceover.replace("…","\\'85") # Replace unicode ellipsis with real thing

		duration = event.duration[3:-4]
		if duration[0] == '0':
			duration = duration[1:]

		# Collapse lines = honour carriage returns as line breaks.
		if collapse_lines:
			voiceover = voiceover.replace('\n',' ')
		else:
			voiceover = voiceover.replace('\n','\\par\n')

		#fs20 = font size: 20/2 = 10pt
		#li600 = indent 600twips

		# Cue Number, Duration, Start --> End
		rtf_content.append("{\\fs20\\b{" + str(count) + '\t' + duration + " seconds \\cf1 \t\t" + event.time_in + " --> " + event.time_out + "}}\n\\par\\par\n")

		# Voice-over. (If you want to change font add \\f1 after the li700)
		rtf_content.append('{\\li700 ' + voiceover + '\\par\n\n}')

		count += 1

	# ... Close the RTF document
	rtf_content.append("\n}")

	# Save the RTF document
	with open(output_filename, "w") as rtf_file:
		for i in rtf_content:
			rtf_file.write(i)


def write_webvtt(output_filename:str, ad_script:list[AdEvent], metadata:AdMetaData, start_from:int = 1, collapse_lines:bool = False):

	"""
	Convert internal format to a webvtt file
	"""

	webvtt_content:list[str] = []
	count:int = start_from

	# Write header
	webvtt_content.append("WEBVTT\n\n")

	# ... Info Block (Metadata)

	if metadata is not None:
		webvtt_content.append(metadata.get_webvtt_info_block())
		webvtt_content.append('\n\n')

	# Write cues
	for event in ad_script:
		try:
			# Adjust Format: 00:00.00
			# Doubtless there's a more efficent way to do this!
			event.time_in = event.time_in[3:]
			event.time_in = event.time_in[0:5] + '.' + event.time_in[6:]

			event.time_out = event.time_out[3:]
			event.time_out = event.time_out[0:5] + '.' + event.time_out[6:]

			webvtt_content.append(event.time_in + " --> " + event.time_out + '\n')
			voiceover = event.voice_over 
			voiceover = voiceover.replace('>','&gt;') # Escape any '>' characters
			webvtt_content.append(voiceover + '\n\n')
		except:
			print("Problem at: ")
			print(event)
	
	# Remove any trailing newlines from the last event
	x:str = webvtt_content.pop().strip()
	webvtt_content.append(x)

	with open(output_filename, "w") as output_file:
		for line in webvtt_content:
			output_file.write(line)


def write_adxml(output_filename:str, ad_script:list[AdEvent], metadata:AdMetaData, start_from:int = 1, collapse_lines:bool = False):

	""" ADXML (Audio Description XML, a custom XML Grammar) Output """

	xml_content:list[str] = []

	xml_content.append("<script>")

	# Write cues
	for event in ad_script:
		try:
			voiceover = event.voice_over 
			voiceover = voiceover.replace('>','&gt;') # Escape any '>' characters
			voiceover.replace('\n','<br>') # Honour line breaks

			duration = event.duration[:12]

			xml_content.append("<div class=\"cue\">\n")
			xml_content.append("\t<div class=\"cuenumber\">" + str(count) + "</div>\n")
			xml_content.append("\t<div class=\"duration\">" + duration + " seconds</div>\n") 
			xml_content.append("\t<div class=\"vo\">\n")
			xml_content.append(voiceover)
			xml_content.append("</div></div>\n\n")

			count += 1

		except:
			print("Problem at: ")
			print(event)
	xml_content.append("</script>")
	with open(output_filename, "w") as output_file:
		for line in html_content:
			output_file.write(line)


def write_html(output_filename:str, ad_script:list[AdEvent], metadata:AdMetaData, start_from:int = 1, collapse_lines:bool = False):
	""" HTML output """

	html_content:list[str] = []
	count:int = start_from

	# Start the head and metadata

	html_content.append("""<!DOCTYPE html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
""")

	if metadata is not None:
		html_content.append(metadata.get_html_metadata())

	# Add a rudimentary style-sheet

	html_content.append("""
<style>
@page { margin-top: .7in; margin-bottom: .58in; padding: 0; }
body { width:30rem; margin: 0px auto; margin-top: 2rem; }
.cue { clear: both; font-family: "courier"; margin-bottom: 2em; page-break-inside: avoid !important; }
.cuenumber, .duration { font-weight: bold; float: left; font-size: 0.8em; }
.cuenumber { display: block; width: 2rem; }
.duration { display: block; width: 10rem; }
.vo { clear: both; padding-top: 0.4em; margin-left: 2rem; }
h1 { font-weight: bold; font-size: 1em; margin-bottom: 2em; text-align: center; }
header { margin-bottom: 2em; text-align: center; }
</style>""")

	html_content.append("\n</head>\n<body>\n")

	if metadata is not None:
		html_content.append("<header><hgroup><h1>" + metadata.title + "</h1>")
		html_content.append("<p>Audio Description Recording Script</p></hgroup></header>")
	else:
		html_content.append("<h1>Script</h1>")

	# Write cues
	for event in ad_script:
		try:
			voiceover = event.voice_over 
			voiceover = voiceover.replace('>','&gt;') # Escape any '>' characters
			voiceover.replace('\n','<br>') # Honour line breaks

			duration = event.duration[:12]
			"""
			duration = duration[:-3]
			if duration[0] == '0':
				duration = duration[1:]
			"""

			html_content.append("<div class=\"cue\">\n")
			html_content.append("\t<div class=\"cuenumber\">" + str(count) + "</div>\n")
			html_content.append("\t<div class=\"duration\">" + duration + " seconds</div>\n") 
			html_content.append("\t<div class=\"vo\">\n")
			html_content.append(voiceover)
			html_content.append("</div></div>\n\n")

			count += 1

		except:
			print("Problem at: ")
			print(event)


	html_content.append("</body>\n</html>")
	with open(output_filename, "w") as output_file:
		for line in html_content:
			output_file.write(line)


def write_markdown(output_filename:str, ad_script:list[AdEvent], metadata:AdMetaData, collapse_lines:bool = False):

	""" Text output, cues only """

	content:list[str] = []

	# Start the head and metadata

	if metadata is not None:
		content.append(metadata.get_markdown_metadata())
		content.append("\n")

	count = 0

	# Write cues
	for event in ad_script:
		try:
			voiceover = event.voice_over 

			voiceover = convert_to_utf(voiceover)

			# Collapse lines = honour carriage returns as line breaks.
			if collapse_lines:
				voiceover = voiceover.replace('\n',' ')

			content.append(voiceover + "\n\n")

			count += 1

		except:
			print("Problem at: ")
			print(event)
			exit()

	with open(output_filename, "w") as output_file:
		for line in content:
			output_file.write(line)

