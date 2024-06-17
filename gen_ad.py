#!/usr/bin/python3

from adlib import *
import argparse

"""
Main CLI interface for adlib.

gen_ad.py csv html rtf srt kyle  

"""


def main():

	# Process command line options:

	# ... create
	parser = argparse.ArgumentParser(description="Convert subtitle file (SRT) for audio-description to various formats.")

	# ... add arguments
	parser.add_argument("file_name", help="The name of the SRT subtitle file to convert")
	parser.add_argument("-m", help="A metadata file in TOML format (optional)", dest='metadata_file', type=str) 
	parser.add_argument("-o", help="Output filename (no extension required)", dest='output_filename', type=str) 
	parser.add_argument('-f', nargs='+', help="List of formats, separated by space. Possible values are: csv, html, rtf, vtt, kyle, md", dest='formats')

	# ... parse
	args = parser.parse_args()


	# Open and read the SRT file

	try:
		file1 = open(args.file_name, 'r')
		lines = file1.readlines()
		file1.close()
	except:
		print("Unable to open file " + args.file_name)
		exit()

	srt_file = parse_srt(lines)


	# Open and read the JSON file

	metadata = None
	filename = None

	if args.metadata_file != None:
		metadata = AdMetaData()
		metadata.load_metadata(args.metadata_file)
		filename = metadata.filename
	else:
		filename = args.output_filename

	# Now convert

	if 'csv' in args.formats:
		write_csv(filename + ".csv", srt_file)
	
	if 'vtt' in args.formats:
		write_webvtt(filename + ".vtt", srt_file, metadata)

	if 'rtf' in args.formats:
		write_rtf(filename + ".rtf", srt_file, metadata)

	if 'html' in args.formats:
		write_html(filename + ".html", srt_file, metadata)

	if 'srt' in args.formats:
		write_srt(filename + ".srt", srt_file)

	if 'kyle' in args.formats:
		# Kyle no like numbered cues
		write_kyle(filename + "-Cues.rtf", srt_file, metadata, False, True)

	if 'md' in args.formats:
		write_markdown(filename + ".md", srt_file, metadata, False)

if __name__ == '__main__':
	main()
