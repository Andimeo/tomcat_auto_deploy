from config import config
import os

module=None
new_dir=None

def get_current_root_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)

def get_module_code_path():
    global module
    return os.path.join(config.get_local_code_path(), 'sgiggle/server/' + module + '/' + module)

def get_module_target_path():
    global module
    return os.path.join(config.get_local_code_path(), 'TARGET/server/' + module)

def get_module_target_file():
    global module
    return os.path.join(get_module_target_path(), module + '.war')

#1. compile local code
def build():
    assert os.path.exists(get_module_code_path())
    if os.path.exists(get_module_target_file()):
        os.remove(get_module_target_file())
        
    os.chdir(get_module_code_path())
    cmd_ant='ant'
    assert os.system(cmd_ant) == 0
    assert os.path.exists(get_module_target_file())
    print '@@@@@@@@@@@@ Build Successful #############'

#2. upload compiled war file
def upload():
    assert os.path.exists(get_module_target_file())
    cmd_scp = 'expect expect/scp_upload.exp "%s" "%s" "%s" "%s" "%s"' % (config.get_dest_username(), config.get_dest_ip(), config.get_dest_password(), get_module_target_file(), config.get_dest_scp_path())
    os.chdir(get_current_root_path())
    assert os.system(cmd_scp) == 0
    print '@@@@@@@@@@@@ Upload Successful #############'


def download_properties():
    cmd_scp = 'expect expect/scp_download.exp  "%s" "%s" "%s" "%s" "%s"' % (config.get_dest_username(), config.get_dest_ip(), config.get_dest_password(), config.get_local_download_path(), config.get_dest_war_path() + '/' + module + '/current/WEB-INF/classes/*.properties')
    assert os.system(cmd_scp) == 0
    print '@@@@@@@@@@@@ Download properties Successful #############'

def upload_properties(properties):
    files = []
    for prop in properties:
        files.append(os.path.join(config.get_local_download_path(), prop))
    cmd_scp = 'expect expect/scp_upload.exp  "%s" "%s" "%s" "%s" "%s"' % (config.get_dest_username(), config.get_dest_ip(), config.get_dest_password(), ' '.join(files), config.get_dest_scp_path())
    assert os.system(cmd_scp) == 0
    print '@@@@@@@@@@@@ Upload properties Successful #############'
    
def move_properties(properties):
    global new_dir
    cmds = []
    for prop in properties:
        cmds.append('mv %s %s' % (os.path.join(config.get_dest_scp_path(), prop), config.get_dest_war_path() + '/' + module + '/' + new_dir + '/WEB-INF/classes'))
    cmd_move = '\n'.join(cmds)
    cmd_ssh = 'expect expect/ssh.exp  "%s" "%s" "%s" "%s"' % (config.get_dest_username(), config.get_dest_password(), config.get_dest_ip(), cmd_move)
    assert os.system(cmd_ssh) == 0
    
#3. merge all properties : take the union of svn version and remote `current` version
def merge_properties():
    global new_dir
    download_properties()
    path = get_module_code_path() + '/WebContent/WEB-INF/classes'
    properties = [x for x in os.listdir(path) if x.endswith('.properties')]
    for prop in properties:
        d = {}
        # User remote `current` as default
        with open(os.path.join(config.get_local_download_path(), prop), 'r') as f:
            for line in f:
                segs = line.strip().split('=')
                if len(segs) >  1 and not segs[0].startswith('#'):
                    key = segs[0]
                    value = ''.join(segs[1:])
                    d[key] = value
        with open(os.path.join(path, prop), 'r') as f:
            for line in f:
                segs = line.strip().split('=')
                if len(segs) > 1 and not segs[0].startswith('#'):
                    key = segs[0]
                    if not d.has_key(key) :
                        value = ''.join(segs[1:])
                        d[key] = value
        with open(os.path.join(config.get_local_download_path(), prop), 'w') as f:
            for key in d:
                line = key + '=' + d[key] + '\n'
                f.write(line)
    upload_properties(properties)
    move_properties(properties)
    
    print '@@@@@@@@@@@@ Merge properties Successful #############'

#3. prepare
def prepare():
    global new_dir
    #1) enter the directory
    cmds = []
    cmd_cd_module_path='cd %s' % os.path.join(config.get_dest_war_path(), module)
    cmds.append(cmd_cd_module_path)
    
    #2) make new directory
    import datetime
    new_dir=datetime.datetime.now().strftime('%m%d_%H%M')
    cmd_make_new_dir='mkdir %s' % new_dir
    cmds.append(cmd_make_new_dir)
    
    #3) decompress
    cmd_decompress_war='cd %s; %s xvf %s' % (new_dir, config.get_dest_java_home() + '/bin/jar', os.path.join(config.get_dest_scp_path(), module + '.war'))
    cmds.append(cmd_decompress_war)
    
    cmd_ssh='expect expect/ssh.exp "%s" "%s" "%s" "%s"' % (config.get_dest_username(), config.get_dest_password(), config.get_dest_ip(), '\n'.join(cmds))
    assert os.system(cmd_ssh) == 0
    
    merge_properties()
    print '@@@@@@@@@@@@ Prepare Successful #############'
    
#4. stop service, change current linking, start service
def deploy():
    global new_dir
    #1) stop service
    from tomcat_manager import TomcatManager
    manager = TomcatManager('http://' + config.get_dest_ip() + ':' + config.get_dest_tomcat_port() + '/manager/text', config.get_dest_tomcat_username(), config.get_dest_tomcat_password())
    manager.stop("/" + module)
    
    #2) change link
    cmds = []
    cmd_rm_current = 'rm %s' % (config.get_dest_war_path() + '/' + module + '/current')
    cmds.append(cmd_rm_current)
    
    cmd_ln_current = 'ln -s %s %s' % (config.get_dest_war_path() + '/' + module + '/' + new_dir, config.get_dest_war_path() + '/' + module + '/current')
    cmds.append(cmd_ln_current)
    
    cmd = 'expect expect/ssh.exp "%s" "%s" "%s" "%s"' % (config.get_dest_username(), config.get_dest_password(), config.get_dest_ip(), '\n'.join(cmds))
    assert os.system(cmd) == 0
    #3) recover service
    manager.start("/" + module)
    print '@@@@@@@@@@@@ Deploy Successful #############'
    
    
if __name__ == '__main__':
    import sys
    module = sys.argv[1]
    #build()
    upload()
    prepare()
    deploy()