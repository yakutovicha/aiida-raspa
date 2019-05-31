# -*- coding: utf-8 -*-
"""Raspa input plugin."""
from __future__ import absolute_import
import os
from shutil import copyfile, copytree
import six
from six.moves import map, range

from aiida.orm import Dict, FolderData, List, RemoteData, SinglefileData
from aiida.common import CalcInfo, CodeInfo, InputValidationError
#from aiida.cmdline.utils import echo
from aiida.engine import CalcJob
from aiida.plugins import DataFactory

from aiida_raspa.utils import RaspaInput

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name


class RaspaCalculation(CalcJob):
    """This is a RaspaCalculation, subclass of CalcJob, to prepare input for RASPA code.
    For information on RASPA, refer to: https://github.com/iraspa/raspa2.
    """
    # Defaults
    INPUT_FILE = 'simulation.input'
    OUTPUT_FOLDER = 'Output'
    RESTART_FOLDER = 'Restart'
    PROJECT_NAME = 'aiida'
    DEFAULT_PARSER = 'raspa'

    @classmethod
    def define(cls, spec):
        super(RaspaCalculation, cls).define(spec)

        #Input parameters
        spec.input('parameters', valid_type=Dict, required=True, help='Input parameters')
        spec.input_namespace('framework', valid_type=CifData, required=False, dynamic=True, help='Input framework(s)')
        spec.input_namespace(
            'block_pocket', valid_type=SinglefileData, required=False, dynamic=True, help='Zeo++ block pocket file')
        spec.input_namespace('file', valid_type=SinglefileData, required=False, help='Additional input file(s)')
        # TODO: understand do `settings` need to be of type `Dict`? Would dict also work?
        spec.input('settings', valid_type=Dict, required=False, help='Additional input parameters')
        spec.input('parent_folder', valid_type=RemoteData, required=False, help='Remote folder used to continue the same simulation stating from the binary restarts.')
        spec.input(
            'retrieved_parent_folder', valid_type=FolderData, required=False, help='To use an old calculation as a starting poing for a new one.')
        spec.input('metadata.options.parser_name', valid_type=six.string_types, default=cls.DEFAULT_PARSER, non_db=True)

        # Output parameters
        spec.output('output_parameters', valid_type=Dict, required=True, help="The results of a calculation")
        spec.output('warnings', valid_type=List, required=False, help="Warnings that appeared during the calculation")

        # Exit codes
        spec.exit_code(
            100, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.')
        spec.exit_code(101, 'ERROR_NO_OUTPUT_FILE', message='The retrieved folder does not contain an output file.')

        # Default output node
        spec.default_output_node = 'output_parameters'

    # --------------------------------------------------------------------------
    # pylint: disable = too-many-locals
    def prepare_for_submission(self, folder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param folder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        """

        # handle input parameters
        parameters = self.inputs.parameters.get_dict()

        # handle framework(s) and/or box(es)
        if "System" in parameters:
            self._handle_system_section(parameters, folder)

        # handle restart
        if 'retrieved_parent_folder' in self.inputs:
            self._handle_retrieved_parent_folder(parameters, folder)

        # handle binary restart
        remote_copy_list = []
        if 'parent_folder' in self.inputs:
            self._handle_parent_folder(parameters, remote_copy_list)

        # Get settings
        if 'setting' in self.inputs:
            settings = self.inputs.settings.get_dict()
        else:
            settings = {}

        # write raspa input file
        inp = RaspaInput(parameters)
        with open(folder.get_abs_path(self.INPUT_FILE), "w") as fobj:
            fobj.write(inp.render())

        # create code info
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = settings.pop('cmdline', []) + [self.INPUT_FILE]
        codeinfo.code_uuid = self.inputs.code.uuid

        # create calc info
        calcinfo = CalcInfo()
        calcinfo.stdin_name = self.INPUT_FILE
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = codeinfo.cmdline_params
        calcinfo.stdin_name = self.INPUT_FILE
        #calcinfo.stdout_name = self.OUTPUT_FILE
        calcinfo.codes_info = [codeinfo]

        # file lists
        calcinfo.remote_symlink_list = []
        calcinfo.local_copy_list = []
        if 'file' in self.inputs:
            for fobj in self.inputs.file.values():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename, fobj.filename))

        # block pockets
        if 'block_pocket' in self.inputs:
            for name, fobj in self.inputs.block_pocket.items():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename, name + '.block'))

        # continue the previous calculation starting from the binary restart
        calcinfo.remote_copy_list = remote_copy_list

        calcinfo.retrieve_list = [self.OUTPUT_FOLDER, self.RESTART_FOLDER]
        calcinfo.retrieve_list += settings.pop('additional_retrieve_list', [])

        # check for left over settings
        if settings:
            raise InputValidationError("The following keys have been found " +
                                       "in the settings input node {}, ".format(self.pk) + "but were not understood: " +
                                       ",".join(list(settings.keys())))

        return calcinfo

    def _handle_system_section(self, parameters, folder):
        """Handle framework(s) and/or box(es)."""
        for name, sparams in parameters["System"].items():
            if sparams["type"] == "Framework":
                try:
                    self.inputs.framework[name].export(folder.get_abs_path(name + '.cif'), fileformat='cif')
                except KeyError:
                    raise InputValidationError(
                        "You specified '{}' framework in the input dictionary, but did not provide the input "
                        "framework with the same name".format(name))

    def _handle_retrieved_parent_folder(self, parameters, folder):
        """Enable restart from the retrieved folder."""
        if "Restart" not in self.inputs.retrieved_parent_folder._repository.list_object_names():  # pylint: disable=protected-access
            raise InputValidationError("Restart was requested but the restart "
                                       "folder was not found in the previos calculation.")
        copytree(
            os.path.join(self.inputs.retrieved_parent_folder._repository._get_base_folder().abspath, "Restart"),  # pylint: disable=protected-access
            folder.get_abs_path("RestartInitial"))
        parameters['GeneralSettings']['RestartFile'] = True

    def _handle_parent_folder(self, parameters, remote_copy_list):
        """Enable binary restart from the remote folder."""
        remote_copy_list.append((self.inputs.parent_folder.computer.uuid,
                                 os.path.join(self.inputs.parent_folder.get_remote_path(), 'CrashRestart'),
                                 'CrashRestart'))
        parameters['GeneralSettings']['ContinueAfterCrash'] = True
