from pathlib import Path
import sys

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print("Usage: {} [folder] [output index file]")
		sys.exit(1)

	folder = sys.argv[1]
	index_file = sys.argv[2]

	files = Path(folder).glob("*.ltlf")
	with Path(index_file).open('w') as f:
		for x in files:
			f.write(x.as_posix())
			f.write("\n")
			f.flush()


