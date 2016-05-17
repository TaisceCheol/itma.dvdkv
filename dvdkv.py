import click,subprocess,os

def get_dvd_mount_point():
	cmd = ['diskutil','info','/dev/disk2']
	diskutil = subprocess.Popen(cmd,stdout=subprocess.PIPE)
	cmd = ['grep','Mount\ Point']
	grep = subprocess.Popen(cmd,stdin=diskutil.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	result,err = grep.communicate()
	return result.split(':')[-1].strip()

def extract_dvd_metadata(info):
	cmd = ['mediainfo','--Output=XML','-f','--Language=raw',info['mnt_point'],'2>&1']
	with open(info['basepath']+'_dvd.metadata.xml', "w") as file:
		subprocess.call(cmd,stdout=file)

def extract_iso_metadata(info)
	cmd = ['mediainfo','--Output=XML','-f','--Language=raw',info['iso_path'],'2>&1']
	with open(info['basepath']+'_iso.metadata.xml', "w") as file:
		subprocess.call(cmd,stdout=file)

def create_iso(info):
	if not os.path.exists(info['writedir']):
		os.mkdir(info['writedir'])
	extract_dvd_metadata()
	info['iso_path'] = info['basepath'] +'.iso'
	cmd = ['dd',info['mnt_point'],info['iso_path']]
	subprocess.call(cmd)
	extract_iso_metadata()


def inquisition():
	info = {}
	info['title'] = click.prompt("Please enter DVD title")
	info['date'] = click.prompt("Please enter date")
	info['refno'] = click.prompt("Please enter REFNO")
	info['objid'] = info['refno'].replace('-','').lower()
	info['write_dir'] = click.prompt("Specify output location")
	info['basepath'] = os.path.join(info['writedir'],info['objid'])
	info['technician'] = click.prompt("Please enter your own name",default="Piaras Hoban")
	info['mnt_point'] = get_dvd_mount_point()
	return info

info = inquisition()

