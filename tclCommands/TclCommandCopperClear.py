from tclCommands.TclCommand import TclCommand

import collections
import logging

import gettext
import FlatCAMTranslation as fcTranslate
import builtins

fcTranslate.apply_language('strings')
if '_' not in builtins.__dict__:
    _ = gettext.gettext

log = logging.getLogger('base')


class TclCommandCopperClear(TclCommand):
    """
    Clear the non-copper areas.
    """

    # Array of all command aliases, to be able use old names for backward compatibility (add_poly, add_polygon)
    aliases = ['ncc_clear', 'ncc']

    # dictionary of types from Tcl command, needs to be ordered
    arg_names = collections.OrderedDict([
        ('name', str),
    ])

    # dictionary of types from Tcl command, needs to be ordered , this  is  for options  like -optionname value
    option_types = collections.OrderedDict([
        ('tooldia', str),
        ('overlap', float),
        ('order', str),
        ('margin', float),
        ('method', str),
        ('connect', bool),
        ('contour', bool),
        ('has_offset', bool),
        ('offset', float),
        ('rest', bool),
        ('all', int),
        ('ref', int),
        ('box', str),
        ('outname', str),
    ])

    # array of mandatory options for current Tcl command: required = {'name','outname'}
    required = ['name']

    # structured help for current command, args needs to be ordered
    help = {
        'main': "Clear excess copper in polygons. Basically it's a negative Paint.",
        'args': collections.OrderedDict([
            ('name', 'Name of the source Geometry object. String.'),
            ('tooldia', 'Diameter of the tool to be used. Can be a comma separated list of diameters. No space is '
                        'allowed between tool diameters. E.g: correct: 0.5,1 / incorrect: 0.5, 1'),
            ('overlap', 'Percentage of tool diameter to overlap current pass over previous pass. Float [0, 99.9999]\n'
                        'E.g: for a 25% from tool diameter overlap use -overlap 25'),
            ('margin', 'Bounding box margin. Float number.'),
            ('order', 'Can have the values: "no", "fwd" and "rev". String.'
                      'It is useful when there are multiple tools in tooldia parameter.'
                      '"no" -> the order used is the one provided.'
                      '"fwd" -> tools are ordered from smallest to biggest.'
                      '"rev" -> tools are ordered from biggest to smallest.'),
            ('method', 'Algorithm for copper clearing. Can be: "standard", "seed" or "lines".'),
            ('connect', 'Draw lines to minimize tool lifts. True or False'),
            ('contour', 'Cut around the perimeter of the painting. True or False'),
            ('rest', 'Use rest-machining. True or False'),
            ('has_offset', 'The offset will used only if this is set True or present in args. True or False.'),
            ('offset', 'The copper clearing will finish to a distance from copper features. Float number.'),
            ('all', 'Will copper clear the whole object. 1 or True = enabled, anything else = disabled'),
            ('ref', 'Will clear of extra copper all polygons within a specified object with the name in "box" '
                    'parameter. 1 or True = enabled, anything else = disabled'),
            ('box', 'Name of the object to be used as reference. Required when selecting "ref" = 1. String.'),
            ('outname', 'Name of the resulting Geometry object. String.'),
        ]),
        'examples': ["ncc obj_name -tooldia 0.3,1 -overlap 10 -margin 1.0 -method 'lines' -all True"]
    }

    def execute(self, args, unnamed_args):
        """
        execute current TCL shell command

        :param args: array of known named arguments and options
        :param unnamed_args: array of other values which were passed into command
            without -somename and  we do not have them in known arg_names
        :return: None or exception
        """

        name = args['name']

        # Get source object.
        try:
            obj = self.app.collection.get_by_name(str(name))
        except Exception as e:
            log.debug("TclCommandCopperClear.execute() --> %s" % str(e))
            self.raise_tcl_error("%s: %s" % (_("Could not retrieve object"), name))
            return "Could not retrieve object: %s" % name

        if obj is None:
            return "Object not found: %s" % name

        if 'tooldia' in args:
            tooldia = str(args['tooldia'])
        else:
            tooldia = self.app.defaults["tools_ncctools"]

        if 'overlap' in args:
            overlap = float(args['overlap']) / 100.0
        else:
            overlap = float(self.app.defaults["tools_nccoverlap"]) / 100.0

        if 'order' in args:
            order = args['order']
        else:
            order = str(self.app.defaults["tools_nccorder"])

        if 'margin' in args:
            margin = float(args['margin'])
        else:
            margin = float(self.app.defaults["tools_nccmargin"])

        if 'method' in args:
            method = args['method']
        else:
            method = str(self.app.defaults["tools_nccmethod"])

        if 'connect' in args:
            connect = bool(args['connect'])
        else:
            connect = eval(str(self.app.defaults["tools_nccconnect"]))

        if 'contour' in args:
            contour = bool(args['contour'])
        else:
            contour = eval(str(self.app.defaults["tools_ncccontour"]))

        offset = 0.0
        if 'has_offset' in args:
            has_offset = bool(args['has_offset'])
            if args['has_offset'] is True:
                if 'offset' in args:
                    offset = float(args['margin'])
                else:
                    # 'offset' has to be in args if 'has_offset' is and it is set True
                    self.raise_tcl_error("%s: %s" % (_("Could not retrieve object"), name))
        else:
            has_offset = False

        try:
            tools = [float(eval(dia)) for dia in tooldia.split(",") if dia != '']
        except AttributeError:
            tools = [float(tooldia)]

        # store here the default data for Geometry Data
        default_data = {}
        default_data.update({
            "name": '_paint',
            "plot": self.app.defaults["geometry_plot"],
            "cutz": self.app.defaults["geometry_cutz"],
            "vtipdia": 0.1,
            "vtipangle": 30,
            "travelz": self.app.defaults["geometry_travelz"],
            "feedrate": self.app.defaults["geometry_feedrate"],
            "feedrate_z": self.app.defaults["geometry_feedrate_z"],
            "feedrate_rapid": self.app.defaults["geometry_feedrate_rapid"],
            "dwell": self.app.defaults["geometry_dwell"],
            "dwelltime": self.app.defaults["geometry_dwelltime"],
            "multidepth": self.app.defaults["geometry_multidepth"],
            "ppname_g": self.app.defaults["geometry_ppname_g"],
            "depthperpass": self.app.defaults["geometry_depthperpass"],
            "extracut": self.app.defaults["geometry_extracut"],
            "extracut_length": self.app.defaults["geometry_extracut_length"],
            "toolchange": self.app.defaults["geometry_toolchange"],
            "toolchangez": self.app.defaults["geometry_toolchangez"],
            "endz": self.app.defaults["geometry_endz"],
            "spindlespeed": self.app.defaults["geometry_spindlespeed"],
            "toolchangexy": self.app.defaults["geometry_toolchangexy"],
            "startz": self.app.defaults["geometry_startz"],

            "tooldia": self.app.defaults["tools_painttooldia"],
            "paintmargin": self.app.defaults["tools_paintmargin"],
            "paintmethod": self.app.defaults["tools_paintmethod"],
            "selectmethod": self.app.defaults["tools_selectmethod"],
            "pathconnect": self.app.defaults["tools_pathconnect"],
            "paintcontour": self.app.defaults["tools_paintcontour"],
            "paintoverlap": self.app.defaults["tools_paintoverlap"]
        })
        ncc_tools = dict()

        tooluid = 0
        for tool in tools:
            tooluid += 1
            ncc_tools.update({
                int(tooluid): {
                    'tooldia': float('%.*f' % (obj.decimals, tool)),
                    'offset': 'Path',
                    'offset_value': 0.0,
                    'type': 'Iso',
                    'tool_type': 'C1',
                    'data': dict(default_data),
                    'solid_geometry': []
                }
            })

        if 'rest' in args:
            rest = bool(args['rest'])
        else:
            rest = eval(str(self.app.defaults["tools_nccrest"]))

        if 'outname' in args:
            outname = args['outname']
        else:
            if rest is True:
                outname = name + "_ncc"
            else:
                outname = name + "_ncc_rm"

        # Non-Copper clear all polygons in the non-copper clear object
        if 'all' in args and bool(args['all']):
            self.app.ncclear_tool.clear_copper_tcl(ncc_obj=obj,
                                                   select_method='itself',
                                                   ncctooldia=tooldia,
                                                   overlap=overlap,
                                                   order=order,
                                                   margin=margin,
                                                   has_offset=has_offset,
                                                   offset=offset,
                                                   method=method,
                                                   outname=outname,
                                                   connect=connect,
                                                   contour=contour,
                                                   rest=rest,
                                                   tools_storage=ncc_tools,
                                                   plot=False,
                                                   run_threaded=False)
            return

        # Non-Copper clear all polygons found within the box object from the the non_copper cleared object
        elif 'ref' in args and bool(args['ref']):
            if 'box' not in args:
                self.raise_tcl_error('%s' % _("Expected -box <value>."))
            else:
                box_name = args['box']

                # Get box source object.
                try:
                    box_obj = self.app.collection.get_by_name(str(box_name))
                except Exception as e:
                    log.debug("TclCommandCopperClear.execute() --> %s" % str(e))
                    self.raise_tcl_error("%s: %s" % (_("Could not retrieve box object"), name))
                    return "Could not retrieve object: %s" % name

                self.app.ncclear_tool.clear_copper_tcl(ncc_obj=obj,
                                                       sel_obj=box_obj,
                                                       select_method='box',
                                                       ncctooldia=tooldia,
                                                       overlap=overlap,
                                                       order=order,
                                                       margin=margin,
                                                       has_offset=has_offset,
                                                       offset=offset,
                                                       method=method,
                                                       outname=outname,
                                                       connect=connect,
                                                       contour=contour,
                                                       rest=rest,
                                                       tools_storage=ncc_tools,
                                                       plot=False,
                                                       run_threaded=False)
            return
        else:
            self.raise_tcl_error("%s:" % _("None of the following args: 'ref', 'all' were found or none was set to 1.\n"
                                           "Copper clearing failed."))
            return "None of the following args: 'ref', 'all' were found or none was set to 1.\n" \
                   "Copper clearing failed."
