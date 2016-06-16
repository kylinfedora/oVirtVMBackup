import os

from ovirtvmbackup import OvirtBackup, rename_clone
from colorama import init, Fore
import argparse
from time import sleep

init(autoreset=True)

path_export = "/exportdomain/"
vms_path = "/master/vms/"
images_path = "/images/"

def get_args():
    '''Function parses and return arguments passed in'''

    parser = argparse.ArgumentParser(
        description='Automatic export/import virtual machine RHEV',
        prog='ovirtbackup')

    parser.add_argument('-v', '--version',
                        action='version', version='%(prog)s 0.3')
    parser.add_argument('--export', help="export virtual machine",
                        action="store_true")
    parser.add_argument('vmname')
    requiredNamed = parser.add_argument_group("required named arguments")
    requiredNamed.add_argument('--manager', help='FQDN manager oVirt/RHEV',
                               required=True)
    requiredNamed.add_argument('--username', help='username with admin privileges',
                               default='admin@internal')
    requiredNamed.add_argument('--password', help='password for the user',
                               required=True)
    requiredNamed.add_argument('--export-domain', metavar="EXPORT", dest="export_name",
                               help='Export Domain Name', required=True)

    args = parser.parse_args()

    return args.export, args.vmname, args.manager, args.username, args.password, args.export_name


def export(conn, vm_name, new_name, description, export_domain):
    print(Fore.GREEN + "Export virtual machine {}".format(vm_name))

    if (conn.if_exists_vm(vm=vm_name)):
        if (conn.if_exists_vm(vm=new_name)):
            print(Fore.RED + "Virtual Machine {} Backup already exists".format(new_name))
        else:
            print(Fore.YELLOW + "creating snapshot")
            conn.create_snap(desc=description, vm=vm_name)
            print(Fore.GREEN + "\ncreate snapshot successful")
            print(Fore.YELLOW + "creating new virtual machine {}".format(new_name))
            conn.create_vm_to_export(vm=vm_name, new_name=new_name, desc=description)
            print(Fore.GREEN + "\ncreate virtual machine {} successful".format(new_name))
            print(Fore.YELLOW + "Activating Export Domain {}".format(export_domain))
            conn.active_export(vm=vm_name, export_name=export_domain)
            print(Fore.GREEN + "Export domain {} successful activated".format(export_domain))
            print(Fore.YELLOW + "Export Virtual Machine {}".format(new_name))
            export_dom = conn.get_export_domain(vm=vm_name)
            conn.export_vm(new_name, export_dom)
            print(Fore.GREEN + "\nExport Virtual Machine {} successful".format(export_domain))
            print(Fore.YELLOW + "Moving export to another location")
            conn.create_dirs(vm_name=vm_name, export_path=path_export, images=images_path, vms=vms_path)
            conn.do_mv(vm=new_name, export_path=path_export, images=images_path, vms=vms_path)
            # trabajado con ovf's
            print(Fore.YELLOW + "Change id's and paths")
            conn.get_running_ovf(vm=vm_name, desc=description, path=path_export)
            export_xml = conn.export_xml_path(path=path_export, vm=vm_name, find_path=vms_path)
            original_xml = conn.export_xml_path(path=path_export, vm=vm_name)
            xml_obj = conn.add_storage_id_xml(original_xml, export_xml)
            ovf_final = os.path.basename(original_xml)[8:]
            vms_path_save = path_export + vm_name + vms_path
            conn.save_new_ovf(path=vms_path_save, name=ovf_final, xml=xml_obj)
            conn.delete_tmp_ovf(path=path_export + vm_name + "/running-" + ovf_final)
            rename_clone(export_xml, vms_path_save + conn.api.vms.get(vm_name).id + "/" + ovf_final, path_export + vm_name + images_path)
            print(Fore.GREEN + "Move successful")
            print(Fore.YELLOW + "Remove snap and Virtual Machine")
            # Eliminando snapshot y {vm}-snap
            conn.delete_snap(vm=vm_name, desc=description)
            conn.delete_tmp_vm(new_name=new_name)
            #  cambiando permisos
            print(Fore.YELLOW + "Applying permissions")
            #conn.change_owner(path=path_export + vm_name)
            print(Fore.GREEN + "process finished successful")
    else:
        print(Fore.RED + "Virtual Machine {} doesn't exists".format(vm_name))

def vm_import(name):
    print("Import virtual machine {}".format(name))
    pass


def main():
    is_export, name, manager, user, password , export_domain = get_args()
    new_name = name + "-snap"
    description = "oVirtBackup"
    url = "https://" + manager
    if is_export is not True:
        print(Fore.RED + "Export option is necesary")
        exit(1)
    else:
        oVirt = OvirtBackup(url, user, password)
        print(Fore.YELLOW + "trying auth...")
        if (oVirt.connect()):
            print(Fore.GREEN + "auth OK")
            export(
                conn=oVirt, vm_name=name, new_name=new_name,
                description=description, export_domain=export_domain
            )

if __name__ == '__main__':
    main()
