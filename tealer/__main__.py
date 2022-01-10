import argparse
import inspect
import sys
import json
from pathlib import Path
from typing import List, Any, Type, Tuple, TYPE_CHECKING, Optional

from pkg_resources import iter_entry_points, require  # type: ignore

from tealer.detectors import all_detectors
from tealer.detectors.abstract_detector import AbstractDetector, DetectorType
from tealer.printers import all_printers
from tealer.printers.abstract_printer import AbstractPrinter
from tealer.teal.parse_teal import parse_teal
from tealer.utils.command_line import output_detectors, output_printers
from tealer.utils.output import cfg_to_dot
from tealer.exceptions import TealerException

if TYPE_CHECKING:
    from tealer.teal.teal import Teal
    from tealer.utils.output import SupportedOutput


def choose_detectors(
    args: argparse.Namespace, all_detector_classes: List[Type[AbstractDetector]]
) -> List[Type[AbstractDetector]]:

    detectors_to_run = []
    detectors = {d.NAME: d for d in all_detector_classes}

    if args.detectors_to_run == "all":
        detectors_to_run = all_detector_classes
    else:
        for detector in args.detectors_to_run.split(","):
            if detector in detectors:
                detectors_to_run.append(detectors[detector])
            else:
                raise TealerException(f"Error: {detector} is not a detector")

    if args.detectors_to_exclude:
        detectors_to_run = [d for d in detectors_to_run if d.NAME not in args.detectors_to_exclude]

    if args.exclude_stateful:
        detectors_to_run = [d for d in detectors_to_run if d.TYPE != DetectorType.STATEFULL]

    if args.exclude_stateless:
        detectors_to_run = [d for d in detectors_to_run if d.TYPE != DetectorType.STATELESS]

    return detectors_to_run


def choose_printers(
    args: argparse.Namespace, all_printer_classes: List[Type[AbstractPrinter]]
) -> List[Type[AbstractPrinter]]:

    if args.printers_to_run is None:
        return []

    printers = {printer.NAME: printer for printer in all_printer_classes}
    printers_to_run = []
    for printer in args.printers_to_run.split(","):
        if printer in printers:
            printers_to_run.append(printers[printer])
        else:
            raise TealerException(f"{printer} is not a printer")
    return printers_to_run


def parse_args(
    detector_classes: List[Type[AbstractDetector]], printer_classes: List[Type[AbstractPrinter]]
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TealAnalyzer",
        usage="tealer program.teal [flag]",
    )

    parser.add_argument("program", help="program.teal")

    parser.add_argument(
        "--version",
        help="displays the current version",
        version=require("tealer")[0].version,
        action="version",
    )

    parser.add_argument(
        "--print-cfg",
        nargs="?",
        help="export cfg in dot format to given file, default cfg.dot",
        const="cfg.dot",
    )

    group_detector = parser.add_argument_group("Detectors")
    group_printer = parser.add_argument_group("Printers")
    group_misc = parser.add_argument_group("Additional options")

    group_detector.add_argument(
        "--list-detectors",
        help="List available detectors",
        action=ListDetectors,
        nargs=0,
        default=False,
    )

    available_detectors = ", ".join(d.NAME for d in detector_classes)
    group_detector.add_argument(
        "--detect",
        help="Comma-separated list of detectors, defaults to all, "
        f"available detectors: {available_detectors}",
        action="store",
        dest="detectors_to_run",
        default="all",
    )

    group_detector.add_argument(
        "--exclude",
        help="Comma-separated list of detectors that should be excluded.",
        action="store",
        dest="detectors_to_exclude",
        default=None,
    )

    group_detector.add_argument(
        "--exclude-stateless",
        help="Exclude detectors of stateless type",
        action="store_true",
        default=False,
    )

    group_detector.add_argument(
        "--exclude-stateful",
        help="Exclude detectors of stateful type",
        action="store_true",
        default=False,
    )

    group_detector.add_argument(
        "--all-paths-in-one",
        help="highlights all the vunerable paths in a single file.",
        action="store_true",
        default=False,
    )

    group_printer.add_argument(
        "--list-printers",
        help="List available printers",
        action=ListPrinters,
        nargs=0,
        default=False,
    )

    available_printers = ", ".join(p.NAME for p in printer_classes)
    group_printer.add_argument(
        "--print",
        help="Comma-separated list of printers, defaults to None,"
        f" available printers: {available_printers}",
        action="store",
        dest="printers_to_run",
        default=None,
    )

    group_misc.add_argument(
        "--json",
        help='Export the results as a JSON file ("--json -" to export to stdout)',
        action="store",
        default=None,
    )

    group_misc.add_argument(
        "--dest",
        help="destination to save the output files, defaults to current directory",
        action="store",
        default=".",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    return args


class ListDetectors(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: argparse.ArgumentParser, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        detectors, _ = get_detectors_and_printers()
        output_detectors(detectors)
        parser.exit()


class ListPrinters(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: argparse.ArgumentParser, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        _, printers = get_detectors_and_printers()
        output_printers(printers)
        parser.exit()


def collect_plugins() -> Tuple[List[Type[AbstractDetector]], List[Type[AbstractPrinter]]]:
    """collect detectors and printers installed in form of plugins.

    plugins are collected using the entry point group `teal_analyzer.plugin`.
    The entry point of each plugin has to return tuple containing list of detectors and
    list of printers defined in the plugin when called.

    Returns:
        (Tuple[List[Type[AbstractDetector]], List[Type[AbstractPrinter]]]): detectors and
        printers added in the form of plugins.

    """
    detector_classes: List[Type[AbstractDetector]] = []
    printer_classes: List[Type[AbstractPrinter]] = []
    for entry_point in iter_entry_points(group="teal_analyzer.plugin", name=None):
        make_plugin = entry_point.load()

        plugin_detectors, plugin_printers = make_plugin()
        detector = None
        if not all(issubclass(detector, AbstractDetector) for detector in plugin_detectors):
            raise TealerException(
                f"Error when loading plugin {entry_point}, {detector} is not a detector"
            )
        printer = None
        if not all(issubclass(printer, AbstractPrinter) for printer in plugin_printers):
            raise TealerException(
                f"Error when loading plugin {entry_point}, {printer} is not a printer"
            )

        detector_classes += plugin_detectors
        printer_classes += plugin_printers

    return detector_classes, printer_classes


def get_detectors_and_printers() -> Tuple[
    List[Type[AbstractDetector]], List[Type[AbstractPrinter]]
]:
    detector_classes = [getattr(all_detectors, name) for name in dir(all_detectors)]
    detector_classes = [
        d for d in detector_classes if inspect.isclass(d) and issubclass(d, AbstractDetector)
    ]

    printer_classes = [getattr(all_printers, name) for name in dir(all_printers)]
    printer_classes = [
        d for d in printer_classes if inspect.isclass(d) and issubclass(d, AbstractPrinter)
    ]

    plugins_detectors, plugins_printers = collect_plugins()

    detector_classes += plugins_detectors
    printer_classes += plugins_printers

    return detector_classes, printer_classes


def handle_print_cfg(args: argparse.Namespace, teal: "Teal") -> None:
    filename = args.print_cfg
    if not filename.endswith(".dot"):
        filename += ".dot"

    filename = Path(args.dest) / Path(filename)
    print(f"\nCFG exported to file: {filename}")
    cfg_to_dot(teal.bbs, filename)


def handle_detectors_and_printers(
    args: argparse.Namespace,
    teal: "Teal",
    detectors: List[Type[AbstractDetector]],
    printers: List[Type[AbstractPrinter]],
) -> Tuple[List["SupportedOutput"], List]:
    for detector_cls in detectors:
        teal.register_detector(detector_cls)

    for printer_cls in printers:
        teal.register_printer(printer_cls)

    return teal.run_detectors(), teal.run_printers(Path(args.dest))


def handle_output(
    args: argparse.Namespace,
    detector_results: List["SupportedOutput"],
    _printer_results: List,
    error: Optional[str],
) -> None:
    if args.json is None:

        if error is not None:
            print(f"Error: {error}")
            sys.exit(-1)

        for output in detector_results:
            output.write_to_files(args.dest, args.all_paths_in_one)
    else:
        json_results = [output.to_json() for output in detector_results]

        json_output = {
            "success": error is not None,
            "error": error,
            "result": json_results,
        }

        if args.json == "-":
            print(json.dumps(json_output, indent=2))
        else:
            filename = Path(args.dest) / Path(args.json)
            print(f"json output is written to {filename}")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json.dumps(json_output, indent=2))


def main() -> None:

    detector_classes, printer_classes = get_detectors_and_printers()
    args = parse_args(detector_classes, printer_classes)

    detector_classes = choose_detectors(args, detector_classes)
    printer_classes = choose_printers(args, printer_classes)

    results_detectors: List["SupportedOutput"] = []
    _results_printers: List = []
    error = None
    try:
        with open(args.program, encoding="utf-8") as f:
            print(f"Analyzing {args.program}")
            teal = parse_teal(f.read())

        if args.print_cfg is not None:
            handle_print_cfg(args, teal)
            return

        results_detectors, _results_printers = handle_detectors_and_printers(
            args, teal, detector_classes, printer_classes
        )

    except TealerException as e:
        error = str(e)

    handle_output(args, results_detectors, _results_printers, error)


if __name__ == "__main__":
    main()
