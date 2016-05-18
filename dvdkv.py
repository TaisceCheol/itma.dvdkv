###															###
### INSPIRED BY https://github.com/hneto/DVD-Video-Archiver	###
###															###

import click,subprocess,os,json,re,glob
from lxml import etree
from datetime import date
from dateparser import date as ddparse

def get_dvd_mount_point():
	cmd = ['diskutil','mount','/dev/disk2']
	subprocess.check_output(cmd)
	cmd = ['diskutil','info','/dev/disk2']
	diskutil = subprocess.Popen(cmd,stdout=subprocess.PIPE)
	cmd = ['grep','Mount\ Point']
	grep = subprocess.Popen(cmd,stdin=diskutil.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	result,err = grep.communicate()
	return result.split(':')[-1].strip()

def extract_dvd_metadata():
	global info
	cmd = ['mediainfo','--Output=XML','-f','--Language=Raw',info['mnt_point'],'2>&1']
	info['dvd_metadata_path'] = os.path.join(info['basedir'],'metadata',info['objid']+'.dvd.xml')
	with open(info['dvd_metadata_path'], "w") as file:
		subprocess.call(cmd,stdout=file)
	cmd = ['openssl','md5',info['mnt_point']]
	with open(os.path.join(info['basedir'],'metadata',info['objid']+'dvd.md5'),'w') as f:
		subprocess.call(cmd,stdout=f)

def extract_iso_metadata():
	global info
	cmd = ['mediainfo','--Output=XML','-f','--Language=Raw',info['iso_path'],'2>&1']
	info['iso_metadata_path'] = os.path.join(info['basedir'],'metadata',info['objid']+'.iso.xml')
	with open(info['iso_metadata_path'], "w") as f:
		subprocess.call(cmd,stdout=f)

def create_structure():
	global info
	if not os.path.exists(info['writedir']):
		os.mkdir(info['writedir'])
	if not os.path.exists(info['basedir']):
		os.mkdir(info['basedir'])
	else:
		# improve here
		os.mkdir(info['basedir']+'disc_2')
		info['basedir'] = info['basedir']+'disc_2'
		info['basepath'] = os.path.join(info['writedir'],info['basedir'],info['objid'])
	for fp in ['iso','mkv','mp4','metadata']:
		os.mkdir(os.path.join(info['basedir'],fp))

def create_iso(rescue=False):
	global info
	# first unmount disk
	cmd = ['diskutil','unmountDisk','/dev/disk2']
	subprocess.check_output(cmd)
	info['iso_path'] = os.path.join(info['basedir'],'iso',info['objid']+'.iso')
	if rescue == True:
		cmd = ['ddrescue','-b2048','-u','-n',info['iso_path'],os.path.join(info['basedir'],'metadata',info['basepath']+'.ddrescue.log')]
	else:
		cmd = ['dd','if=/dev/disk2','of=%s'%info['iso_path']]
	subprocess.call(cmd)
	#checksum
	cmd = ['openssl','md5',info['iso_path']]
	with open(info['iso_path']+'.md5' ,'w') as f:
		subprocess.call(cmd,stdout=f)

def create_dvd_file_list():
	'''requires lsdvd and dvd2concat
	lsdvd: https://sourceforge.net/projects/lsdvd/files/lsdvd/lsdvd-0.17.tar.gz/
	cd ~/downloads
	tar -xf lsdvd-0.17.tar.gz
	cd lsdvd-0.17
	./configure
	make
	sudo make install
	dvd2concat is part of ffmepg/tools'''
	global info
	info['filelist'] = info['basepath']+'.filelist.concat'
	# mount iso
	cmd = ['hdiutil','mount',info['iso_path']]
	iso_mnt_dir = re.search(ur"(?P<path>/Volumes/.*)",subprocess.check_output(cmd)).group('path')
	cmd = ['dvd2concat',iso_mnt_dir]
	with open(info['filelist'],'w') as f:
		subprocess.call(cmd,stdout=f)
	# clean up
	cmd = ['hdiutil','eject',info['iso_path']]
	subprocess.call(cmd)

def create_mkv():
	global info
	info['filelist'] = info['basepath']+'.filelist.concat'
	cmd = ['ffmpeg',
		'-safe','0',
		'-protocol_whitelist','subfile,file,crypto,concat', '-f','concat',
		'-i',info['filelist'],
		'-c:v','copy',
		'-c:a','copy','-ac','2',
		'-f','matroska',
		'-y',
		os.path.join(info['basedir'],'mkv',info['objid'] + '.mkv')
	]
	subprocess.call(cmd)
	cmd = ['openssl','md5',os.path.join(info['basedir'],'mkv',info['objid'] + '.mkv')]
	with open(os.path.join(info['basedir'],'mkv',info['objid'] + '.mkv.md5'),"w") as f:
		subprocess.call(cmd,stdout=f)
def create_mp4():
	global info
	cmd = ['ffmpeg',
		'-i',os.path.join(info['basedir'],'mkv',info['objid'] + '.mkv'),
		'-c:v','libx264',
		'-pix_fmt','yuv420p',
		'-c:a','copy','-ac','2',
		'-f','mp4',
		os.path.join(info['basedir'],'mp4',info['objid'] + '.mp4')
	]
	subprocess.call(cmd)
	cmd = ['openssl','md5',os.path.join(info['basedir'],'mp4',info['objid'] + '.mp4')]
	with open(os.path.join(info['basedir'],'mp4',info['objid'] + '.mp4.md5'),"w") as f:
		subprocess.call(cmd,stdout=f)

def process_date(datestr):
	date_obj = ddparse.DateDataParser().get_date_data(datestr)
	if date_obj['period'] == 'year':
		return date_obj['date_obj'].isoformat()[0:4]
	elif date_obj['period'] == 'month':
		return date_obj['date_obj'].isoformat()[0:7]
	elif date_obj['period'] == 'day':
		return date_obj['date_obj'].isoformat()[0:10]
	else:
		return datestr

def write_mods():
	global info
	mods_path = info['basedir']+'/metadata/mods.xml'
	skeleton = """
		<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
			<mods:titleInfo>
				<mods:title>%s</mods:title>
			</mods:titleInfo>
			<mods:originInfo eventType="creation">
				<mods:dateIssued encoding='w3cdtf'>%s</mods:dateIssued>
			</mods:originInfo>
			<mods:identifier type="local">%s</mods:identifier>
			<mods:note type="statement of responsibility">%s</mods:note>
			<mods:note type="technician">%s</mods:note>
			<mods:recordInfo>
				<mods:recordContentSource>DVD</mods:recordContentSource>
				<mods:recordCreationDate encoding='w3cdtf'>%s</mods:recordCreationDate>
			</mods:recordInfo>
		</mods:mods>
	""" % (info['title'],process_date(info['date']),info['refno'],info['performers'],info['technician'],date.today().isoformat())
	p = etree.XMLParser(remove_blank_text=True)
	mods_xml = etree.fromstring(skeleton,parser=p)
	etree.ElementTree(mods_xml).write(mods_path,pretty_print=True,encoding='UTF-8')

def inquisition(writedir):
	global info
	info = {}
	info['title'] = click.prompt(click.style("Please enter DVD title",fg='green'),default="10th William Kennedy Piping Festival: Uilleann Pipes Recital")
	info['date'] = click.prompt(click.style("Please enter date",fg='green'),default="23 November 2003")
	info['performers'] = click.prompt(click.style("Please performers",fg='green'),default='[various performers]')
	info['refno'] = click.prompt(click.style("Please enter REFNO",fg='green'),default='203-ITMA-DVD')
	info['objid'] = info['refno'].replace('-','').lower()
	info['writedir'] = writedir
	info['basedir'] = os.path.join(info['writedir'],info['objid'])
	info['basepath'] = os.path.join(info['writedir'],info['objid'],info['objid'])
	info['technician'] = click.prompt(click.style("Please enter your own name",fg='green'),default="Piaras Hoban")
	info['mnt_point'] = get_dvd_mount_point()
	click.echo(click.style('Information gathered:',fg='blue'))
	print json.dumps(info,indent=True)

@click.command()
@click.option('--writedir',envvar='WRITEDIR',help="Specify the root directory for output.")
@click.option('--rescue',default=False,help="Create .iso using ddrescue otherwise use dd. dd will be faster but ddrescue will help with errors.")
def run(writedir,rescue):
	inquisition(writedir)
	processes = [create_structure,write_mods,extract_dvd_metadata,create_iso,extract_iso_metadata,create_dvd_file_list,create_mkv,create_mp4]
	with click.progressbar(processes[-2:]) as bar:
		for proc in bar:
			proc()


if __name__ == '__main__':
	click.clear()
	banner = """#############################################################\n### Irish Traditional Music Archive :: DVD Archiving Tool ###\n#############################################################\n\n"""
	click.echo(click.style(banner,fg='white'))
	run()
