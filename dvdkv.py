###															###
### INSPIRED BY https://github.com/hneto/DVD-Video-Archiver	###
###															###

import click,subprocess,os,json,re,glob
from lxml import etree

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
	with open(info['basepath']+'.dvd.xml', "w") as file:
		subprocess.call(cmd,stdout=file)

def extract_iso_metadata():
	global info
	cmd = ['mediainfo','--Output=XML','-f','--Language=raw',info['iso_path'],'2>&1']
	with open(info['basepath']+'.iso.xml', "w") as file:
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
	cmd = ['ddrescue','-b2048','-n',info['iso_path'],info['basepath']+'.ddrescue.log']
	subprocess.call(cmd)

def create_dvd_file_list():
	'''
	requires lsdvd and dvd2concat
	lsdvd: https://sourceforge.net/projects/lsdvd/files/lsdvd/lsdvd-0.17.tar.gz/
	cd ~/downloads
	tar -xf lsdvd-0.17.tar.gz
	cd lsdvd-0.17
	./configure
	make
	sudo make install
	dvd2concat is part of ffmepg/tools
	'''
	global info
	info['filelist'] = info['basepath']+'.filelist.concat'
	# mount iso
	cmd = ['hdiutil','mount',info['iso_path']]
	iso_mnt_dir = re.search(ur"(?P<path>/Volumes/.*)",subprocess.check_output(cmd)).group('path')
	cmd = ['dvd2concat',iso_mnt_dir]
	with open(info[filelist],'w') as f:
		subprocess.cmd(cmd,stdout=f)
	# clean up
	cmd = ['hdiutil','eject',info['iso_path']]
	subprocess.call(cmd)

def create_mkv():
	global info
	dvd_metadata = etree.parse(info['basepath']+'.dvd.xml')
	aspect_ratio = dvd_metadata.xpath('/Mediainfo/File/track[@type="Video"]/Display_aspect_ratio/text()')[0]
	cmd = ['ffmpeg',
	'-safe','0',
	'-protocol_whitelist','subfile,file,crypto',
	'-f','concat',
	'-i',info['filelist'],
	'-aspect',aspect_ratio,
	'-c:v','ffv1',
	'-c:a','copy','-ac','2',
	'-f','matroska',
	'-y',
	info['basepath'] + '.mkv'
	]
	subprocess.call(cmd)

def create_mp4():
	global info
	cmd = ['ffmpeg','-i',info['basepath'] + '.mkv','-c:v','libx264','-pix_fmt','yuv420p','-c:a','copy','-ac','2','-f','mp4',info['basepath']+'.mp4']
	subprocess.call(cmd)

def inquisition(writedir):
	global info
	info = {}
	info['title'] = click.prompt(click.style("Please enter DVD title",fg='green'),default='test')
	info['date'] = click.prompt(click.style("Please enter date",fg='green'),default='today')
	info['refno'] = click.prompt(click.style("Please enter REFNO",fg='green'),default='203itmadvd')
	info['objid'] = info['refno'].replace('-','').lower()
	info['writedir'] = writedir
	info['basedir'] = os.path.join(info['writedir'],info['objid'])
	info['basepath'] = os.path.join(info['writedir'],info['objid'],info['objid'])
	info['technician'] = click.prompt(click.style("Please enter your own name",fg='green'),default="Piaras Hoban")
	info['mnt_point'] = get_dvd_mount_point()
	print info['mnt_point']
	click.echo(click.style('Information gathered:',fg='blue'))
	print json.dumps(info,indent=True)

@click.command()
@click.option('--writedir',envvar='WRITEDIR')
def run(writedir):
	inquisition(writedir)
	create_structure()
	extract_dvd_metadata()
	create_iso()
	extract_iso_metadata()
	create_dvd_file_list()
	create_mkv()
	create_mp4()
if __name__ == '__main__':
	run()
