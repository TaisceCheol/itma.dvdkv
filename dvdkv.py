###															###
### INSPIRED BY https://github.com/hneto/DVD-Video-Archiver	###
###															###

import click,subprocess,os,json

def get_dvd_mount_point():
	cmd = ['diskutil','info','/dev/disk2']
	diskutil = subprocess.Popen(cmd,stdout=subprocess.PIPE)
	cmd = ['grep','Mount\ Point']
	grep = subprocess.Popen(cmd,stdin=diskutil.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	result,err = grep.communicate()
	return result.split(':')[-1].strip()

def extract_dvd_metadata():
	global info
	cmd = ['mediainfo','--Output=XML','-f','--Language=raw',info['mnt_point'],'2>&1']
	with open(info['basepath']+'_dvd.metadata.xml', "w") as file:
		subprocess.call(cmd,stdout=file)

def extract_iso_metadata():
	global info
	cmd = ['mediainfo','--Output=XML','-f','--Language=raw',info['iso_path'],'2>&1']

	with open(info['basepath']+'_iso.metadata.xml', "w") as file:
		subprocess.call(cmd,stdout=file)

def create_structure():
	global info
	if not os.path.exists(info['writedir']):
		os.mkdir(info['writedir'])
	if not os.path.exists(info['basedir']):
		os.mkdir(info['basedir'])

def create_iso():
	global info
	# first unmount disk
	cmd = ['diskutil','unmountDisk','/dev/disk2']
	subprocess.call(cmd)
	info['iso_path'] = info['basepath'] +'.iso'
	cmd = ['dd','if=/dev/disk2','of=%s'%info['iso_path']]
	subprocess.call(cmd)

def create_mkv():
	global info
	cmd = ['ffmpeg',
	'-i',info['iso_path'],
	'-vcodec','ffv1',
	'-acodec','copy','-ac','2',
	'-scodec','copy',
	'-f',info['basepath'] + '.mkv'
	]

def inquisition(writedir):
	global info
	info = {}
	info['title'] = click.prompt(click.style("Please enter DVD title",fg='green'))
	info['date'] = click.prompt(click.style("Please enter date",fg='green'))
	info['refno'] = click.prompt(click.style("Please enter REFNO",fg='green'))
	info['objid'] = info['refno'].replace('-','').lower()
	info['writedir'] = writedir
	info['basedir'] = os.path.join(info['writedir'],info['objid'])
	info['basepath'] = os.path.join(info['writedir'],info['objid'],info['objid'])
	info['technician'] = click.prompt(click.style("Please enter your own name",fg='green'),default="Piaras Hoban")
	info['mnt_point'] = get_dvd_mount_point()
	click.echo(click.style('Information gathered:',fg='blue'))
	print json.dumps(info,indent=True)

@click.command()
@click.option('--writedir',envvar='WRITEDIR')
def run(writedir):
	inquisition(writedir)
	create_structure()
	create_iso()

if __name__ == '__main__':
	run()
