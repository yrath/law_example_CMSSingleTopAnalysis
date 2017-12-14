# -*- coding: utf-8 -*-

"""
TODO.
"""


from collections import OrderedDict

import law
import six

from analysis.framework.tasks import ConfigTask, DatasetTask
from analysis.framework.selection import select_singleTop as select
from analysis.framework.reconstruction import reconstruct_singleTop as reconstruct
from analysis.framework.systematics import apply_jer
from analysis.framework.plotting import stack_plot
from analysis.framework.util import join_struct_arrays
import analysis.setup.singleTop


class FetchData(DatasetTask):

    def output(self):
        return law.LocalFileTarget(self.local_path("data.root"))

    @law.decorator.log
    def run(self):
        output = self.output()
        output.parent.touch()

        # fetch the input file
        src = self.dataset_info_inst.keys[0]
        six.moves.urllib.request.urlretrieve(src, output.path)


class ConvertData(DatasetTask):

    sandbox = "docker::riga/law_example_base"
    force_sandbox = True

    def requires(self):
        return FetchData.req(self)

    def output(self):
        return law.LocalFileTarget(self.local_path("data.npz"))

    @law.decorator.log
    def run(self):
        import root_numpy as rnp

        output = self.output()
        output.parent.touch()

        output.dump(events=rnp.root2array(self.input().path))


class VaryJER(DatasetTask):

    shifts = {"jer_up", "jer_down"}

    sandbox = "docker::riga/law_example_base"
    force_sandbox = True

    def requires(self):
        return ConvertData.req(self)

    def output(self):
        return law.LocalFileTarget(self.local_path("data.npz"))

    @law.decorator.log
    def run(self):
        events = self.input().load()["events"]

        # apply jer to all events
        apply_jer(events, self.shift_inst.direction)

        output = self.output()
        output.parent.touch()
        output.dump(events=events)


class SelectAndReconstruct(DatasetTask):

    shifts = VaryJER.shifts

    sandbox = "docker::riga/law_example_base"
    force_sandbox = True

    def requires(self):
        cls = ConvertData if self.shift_inst.is_nominal else VaryJER
        return cls.req(self)

    def output(self):
        return law.LocalFileTarget(self.local_path("data.npz"))

    @law.decorator.log
    def run(self):
        events = self.input().load()["events"]

        # selection
        indexes, selected_objects = select(events)
        self.publish_message("selected {} of {} events".format(len(indexes), len(events)))
        events = events[indexes]

        # reconstruction
        reco_data = reconstruct(events, selected_objects)
        self.publish_message("reconstructed {} variables".format(len(reco_data.dtype.names)))
        events = join_struct_arrays(events, reco_data)

        output = self.output()
        output.parent.touch()
        output.dump(events=events)


class CreateHistograms(ConfigTask):

    shifts = VaryJER.shifts

    # sandbox = "docker::riga/law_example_base"
    # force_sandbox = True

    def requires(self):
        reqs = OrderedDict()
        for dataset in self.config_inst.datasets:
            reqs[dataset] = SelectAndReconstruct.req(self, dataset=dataset.name)
        return reqs

    def output(self):
        return law.LocalFileTarget(self.local_path("hists.tgz"))

    @law.decorator.log
    def run(self):
        import matplotlib
        matplotlib.use("AGG")
        import matplotlib.pyplot as plt

        # load input arrays per dataset, map them to the first linked process
        events = OrderedDict()
        for dataset, inp in self.input().items():
            process = list(dataset.processes.values())[0]
            events[process] = inp.load()["events"]
            self.publish_message("loaded events for dataset {}".format(dataset.name))

        tmp = law.LocalDirectoryTarget(is_tmp=True)
        tmp.touch()

        for variable in self.config_inst.variables:
            stack_plot(events, variable, tmp.child(variable.name + ".pdf", "f").path)

        output = self.output()
        output.parent.touch()
        output.dump(tmp)
