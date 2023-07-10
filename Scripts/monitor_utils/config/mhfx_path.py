'''
For Menhir FX
author:
Angele Sionneau - asionneau@artfx.fr
'''

user_data_dir = 'U:/mesDocuments/HoursTrackerV2/' # where all the user data will be store. By default U:/mesDocuments
user_tmp_dir = user_data_dir + '/tmp' # where the temporary files will be store. 

# all data file path
user_data_json = user_data_dir + 'hours.json'
user_data_js = user_data_dir + 'hours.js'
user_data_html = user_data_dir + 'hours.html'
user_data_css = user_data_dir + 'style.css'
user_data_backup = user_data_dir + 'backup/'
user_list_backup_json = user_data_dir + 'backups.json'
user_list_backup_js = user_data_dir + 'backups.js'
user_log = user_data_dir + 'log_hourstracker.txt'
user_tmp_processes = user_tmp_dir + '/processes.json'
user_config = user_data_dir + 'config.ini'

# template to get file properties according to the pipe
file_template = "{letter}/{project_name}/03_Production/{asset_type}/{asset_subtype}/{asset_name}/Scenefiles/{department}/{task}/{file}.{ext}"
file_template_bonus = "{letter}/{project_name}/03_Production/{asset_type}/{asset_name}/Scenefiles/{department}/{task}/{file}.{ext}"
