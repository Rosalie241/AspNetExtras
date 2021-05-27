import sublime
import sublime_plugin
import os
import subprocess
import threading
import glob

# simple helper function
# to launch process in a different thread
# with a callback
LaunchProcess_lock = threading.Lock()
def LaunchProcess(on_exit, command, cwd):
	def run_in_thread(on_exit, command, cwd):
		if LaunchProcess_lock.locked():
			sublime.message_dialog("process already running!")
			return

		try:
			LaunchProcess_lock.acquire()

			print("AspNetExtras: -> " + " ".join(command))
	
			process = subprocess.Popen(command,
	        	shell=True, 
				cwd=cwd,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE)
	
			# output each line
			for line in iter(process.stdout.readline, b''):
				print("AspNetExtras: " + line.decode().strip())
	
			# wait until process is done
			process.wait()
	
			print("AspNetExtras: <- " + " ".join(command))
	
			# run callback
			on_exit(command, process.returncode)
		finally:
			LaunchProcess_lock.release()

		return

	# create thread and start it
	thread = threading.Thread(target=run_in_thread, args=(on_exit, command, cwd))
	thread.start()
	return

# simple helper function
# for getting required settings
def GetSetting(settings, key):
	if not settings.has(key):
		sublime.error_message("Please configure \'" + key + "\' in your project settings");
		return None
	return settings.get(key)

# simple helper function
# for getting required project path
def GetProjectDir(window):
	project_path = window.extract_variables()
	if 'project_path' not in project_path:
		sublime.error_message("Please open a project!")
		return None
	return project_path["project_path"]

# simple helper function
# for getting the full path to the aspnet project
def GetAspnetProjectDir(window, settings):
	project_path = GetProjectDir(window)
	if project_path == None:
		return None

	aspnet_project_dir = GetSetting(settings, 'aspnet_extras_project_directory')
	if aspnet_project_dir == None:
		return None

	return os.path.join(project_path, aspnet_project_dir)

def ProcessCallback(command, returncode):
	command_str = " ".join(command)
	if returncode != 0:
		sublime.error_message("\'" + command_str + "\'' Failed!\nView the console for more details")

class MigrationNameInputHandler(sublime_plugin.TextInputHandler):
	def description(self, text):
		return "Migration Name"

	def placeholder(self):
		return self.description("")

class RazorpageNameInputHandler(sublime_plugin.TextInputHandler):
	def description(self, text):
		return "Razor Page Name"

	def placeholder(self):
		return self.description("")

class RazorpageDirInputHandler(sublime_plugin.TextInputHandler):
	def description(self, text):
		return "Razor Page Directory"

	def placeholder(self):
		return self.description("")

class RazorpageNamespaceInputHandler(sublime_plugin.TextInputHandler):
	def description(self, text):
		return "Razor Page Namespace"

	def placeholder(self):
		return self.description("")

class ListItemsInputHandler(sublime_plugin.ListInputHandler):
	items = [ ]

	def set_items(self, items_list):
		self.items = items_list

	def list_items(self):
		return self.items;

class AspnetAddDatabaseMigrationCommand(sublime_plugin.TextCommand):
	def run(self, edit, migration_name):
		project_path = GetAspnetProjectDir(self.view.window(), self.view.settings())
		if project_path == None:
			return

		if migration_name == None or not migration_name:
			sublime.error_message("name cannot be empty")
			return

		LaunchProcess(ProcessCallback,
			["dotnet", "ef", "migrations", "add", migration_name],
			project_path)

		return

	def input(self, args):
		if 'migration_name' not in args:
			return MigrationNameInputHandler()

	def description(self):
		return "Adds a database migration"

class AspnetRemoveDatabaseMigrationCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		project_path = GetAspnetProjectDir(self.view.window(), self.view.settings())
		if project_path == None:
			return

		LaunchProcess(ProcessCallback,
			["dotnet", "ef", "migrations", "remove"],
			project_path)

		return

	def description(self):
		return "Removes a database migration"

class AspnetUpdateDatabaseCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		project_path = GetAspnetProjectDir(self.view.window(), self.view.settings())
		if project_path == None:
			return

		LaunchProcess(ProcessCallback,
			["dotnet", "ef", "database", "update"],
			project_path)

		return

	def description(self):
		return "Updates the database"

class AspnetUpdateDatabaseMigrationCommand(sublime_plugin.TextCommand):
	def get_migrations(self):
		project_path = GetAspnetProjectDir(self.view.window(), self.view.settings())
		if project_path == None:
			return None

		migrations = [ ]
		for f in glob.glob(os.path.join(project_path, "Migrations", "*.cs")):
			file_name = os.path.basename(f)
			if '_' in file_name and 'Designer' not in file_name:
				file_name = os.path.splitext(file_name)[0]
				migrations.append(file_name)

		return migrations

	def run(self, edit, list_items):
		project_path = GetAspnetProjectDir(self.view.window(), self.view.settings())
		if project_path == None:
			return

		LaunchProcess(ProcessCallback,
			["dotnet", "ef", "database", "update", list_items],
			project_path)

		return

	def input(self, args):
		if 'list_items' not in args:
			migrations = self.get_migrations()
			if migrations == None:
				sublime.error_message("No migrations found!");
				return;

			input_handler = ListItemsInputHandler()
			input_handler.set_items(migrations)
			return input_handler

	def description(self):
		return "Updates the database to a migration"

class AspnetDropDatabaseCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		project_path = GetAspnetProjectDir(self.view.window(), self.view.settings())
		if project_path == None:
			return

		LaunchProcess(ProcessCallback,
			["dotnet", "ef", "database", "drop"],
			project_path)

		return

	def description(self):
		return "Drops the database"


class AspnetAddRazorPageCommand(sublime_plugin.TextCommand):
	def run(self, edit, razorpage_name, razorpage_dir, razorpage_namespace):
		project_path = GetAspnetProjectDir(self.view.window(), self.view.settings())
		if project_path == None:
			return

		if razorpage_name == None or not razorpage_name:
			sublime.error_message("name cannot be empty")
			return

		if razorpage_dir == None or not razorpage_dir:
			sublime.error_message("directory cannot be empty")
			return

		if razorpage_namespace == None or not razorpage_namespace:
			sublime.error_message("namespace cannot be empty")
			return

		LaunchProcess(ProcessCallback,
			["dotnet", "new", "page", 
				"--name", razorpage_name,
				"-o", razorpage_dir,
				"-na", razorpage_namespace],
			project_path)

		return

	def input(self, args):
		if 'razorpage_name' not in args:
			return RazorpageNameInputHandler()
		if 'razorpage_dir' not in args:
			return RazorpageDirInputHandler()
		if 'razorpage_namespace' not in args:
			return RazorpageNamespaceInputHandler()

	def description(self):
		return "Adds a razor page"

