# -*- coding: utf-8 -*-
"""Raspa output parser."""
import os

from aiida.common import NotExistent, OutputParsingError
from aiida.engine import ExitCode
from aiida.orm import Dict, List
from aiida.parsers.parser import Parser
from aiida_raspa.utils import parse_base_output_fobj

# parser
# --------------------------------------------------------------------------------------------


class RaspaParser(Parser):
    """Parse RASPA output"""

    # --------------------------------------------------------------------------
    def parse(self, **kwargs):  # pylint: disable=too-many-locals
        """Receives in input a dictionary of retrieved nodes. Does all the logic here."""
        try:
            self.retrieved
        except NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER
        output_folder_name = self.node.process_class.OUTPUT_FOLDER

        if output_folder_name not in self.retrieved.list_object_names():
            return self.exit_codes.ERROR_NO_OUTPUT_FILE

        output_parameters = {}
        warnings = []
        ncomponents = len(self.node.inputs.parameters.get_dict()['Component'])
        for system_id, system_name in enumerate(self.node.get_extra('system_order')):
            # specify the name for the system
            system = "System_{}".format(system_id)
            fname = self.retrieved.list_object_names(os.path.join(output_folder_name, system))[0]  # pylint: disable=protected-access

            # get absolute path of the output file
            with self.retrieved.open(os.path.join(system, fname)) as fobj:
                content = fobj.read()
                if "Starting simulation" not in content:
                    return self.exit_codes.ERROR_SIMULATION_DID_NOT_START
                if "Simulation finished" not in content:
                    return self.exit_codes.TIMEOUT

                # parse output parameters and warnings
                parsed_parameters, parsed_warnings = parse_base_output_fobj(fobj, system_name, ncomponents)
                output_parameters[system_name] = parsed_parameters
                warnings += parsed_warnings

        self.out("output_parameters", Dict(dict=output_parameters))
        self.out("warnings", List(list=warnings))

        return ExitCode(0)
