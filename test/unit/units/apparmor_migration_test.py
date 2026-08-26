import os
from unittest.mock import patch, call, Mock
from pytest import raises
from tempfile import NamedTemporaryFile, TemporaryDirectory

from suse_migration_services.units.apparmor_migration import main
from suse_migration_services.exceptions import DistMigrationAppArmorMigrationException
from suse_migration_services.drop_components import DropComponents


@patch('suse_migration_services.logger.Logger.setup')
class TestAppArmorMigration(object):
    @patch('suse_migration_services.drop_components.MigrationConfig')
    @patch('suse_migration_services.zypper.Zypper.install')
    @patch('suse_migration_services.defaults.Defaults.get_grub_default_file')
    @patch('suse_migration_services.defaults.Defaults.get_selinux_autorelabel_file')
    @patch.object(DropComponents, 'package_installed')
    def test_main(
        self,
        mock_package_installed,
        mock_get_selinux_autorelabel_file,
        mock_get_grub_default_file,
        mock_Zypper_install,
        mock_MigrationConfig,
        mock_logger_setup,
    ):
        migration_config = Mock()
        migration_config.get_zypper_migrate_args.return_value = []
        migration_config.get_zypper_install_args.return_value = []
        mock_MigrationConfig.return_value = migration_config
        mock_package_installed.return_value = True
        test_data = NamedTemporaryFile()
        with open(test_data.name, 'w') as f:
            f.write('GRUB_CMDLINE_LINUX_DEFAULT="splash=silent security=apparmor"')
        mock_get_grub_default_file.return_value = test_data.name
        with TemporaryDirectory() as selinux_dir:
            autorelabel_file = os.sep.join([selinux_dir, '.autorelabel'])
            mock_get_selinux_autorelabel_file.return_value = autorelabel_file
            main()
            assert os.path.exists(autorelabel_file)
        with open(test_data.name) as f:
            assert f.read() == 'GRUB_CMDLINE_LINUX_DEFAULT="splash=silent security=selinux"'
        assert mock_Zypper_install.call_args_list == [
            call(
                'patterns-base-selinux',
                extra_args=['--no-recommends'],
                raise_on_error=False,
                chroot='/system-root',
            ),
            call(
                'venv-salt-minion',
                extra_args=['--force'],
                raise_on_error=False,
                chroot='/system-root',
            ),
        ]

    @patch('suse_migration_services.drop_components.MigrationConfig')
    @patch('suse_migration_services.zypper.Zypper.install')
    @patch('suse_migration_services.defaults.Defaults.get_grub_default_file')
    @patch('suse_migration_services.defaults.Defaults.get_selinux_autorelabel_file')
    @patch.object(DropComponents, 'package_installed')
    def test_main_no_selinux_directory(
        self,
        mock_package_installed,
        mock_get_selinux_autorelabel_file,
        mock_get_grub_default_file,
        mock_Zypper_install,
        mock_MigrationConfig,
        mock_logger_setup,
    ):
        migration_config = Mock()
        migration_config.get_zypper_migrate_args.return_value = []
        migration_config.get_zypper_install_args.return_value = []
        mock_MigrationConfig.return_value = migration_config
        mock_package_installed.return_value = False
        test_data = NamedTemporaryFile()
        mock_get_grub_default_file.return_value = test_data.name
        with TemporaryDirectory() as tmp_dir:
            autorelabel_file = os.sep.join([tmp_dir, 'selinux', '.autorelabel'])
            mock_get_selinux_autorelabel_file.return_value = autorelabel_file
            main()
            assert not os.path.exists(autorelabel_file)

    @patch('suse_migration_services.drop_components.MigrationConfig')
    @patch('fileinput.input')
    def test_main_raises(self, mock_fileinput, mock_MigrationConfig, mock_logger_setup):
        migration_config = Mock()
        migration_config.get_zypper_migrate_args.return_value = []
        migration_config.get_zypper_install_args.return_value = []
        mock_MigrationConfig.return_value = migration_config
        mock_fileinput.side_effect = Exception('error')
        with raises(DistMigrationAppArmorMigrationException):
            main()
