import json, os

    
class Config:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir + '/config/info.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def get_dest_ip(self):
        return self.config['dest']['ip']
    
    def get_dest_username(self):
        return self.config['dest']['username']
    
    def get_dest_password(self):
        return self.config['dest']['password']
    
    def get_dest_tomcat_port(self):
        return self.config['dest']['tomcat']['port']
    
    def get_dest_tomcat_username(self):
        return self.config['dest']['tomcat']['username']
    
    def get_dest_tomcat_password(self):
        return self.config['dest']['tomcat']['password']
    
    def get_dest_scp_path(self):
        return self.config['dest']['scp_path']
    
    def get_dest_war_path(self):
        return self.config['dest']['war_path']
    
    def get_dest_war_name_rule(self):
        return self.config['dest']['war_name_rule']
    
    def get_dest_java_home(self):
        return self.config['dest']['java_home']
    
    def get_local_code_path(self):
        return self.config['local']['code_path']
    
    def get_local_download_path(self):
        return self.config['local']['download_path']

config=Config()