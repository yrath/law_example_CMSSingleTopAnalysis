# -*- coding: utf-8 -*-

"""
Single top analysis definition including config for 2011 Open Data @ 7 TeV.
"""

__all__ = ["analysis_singletop", "config_singletop_opendata_2011"]


import order as od

from analysis.setup.opendata_2011 import campaign_opendata_2011


#
# define analysis
# 

analysis_singletop = ana = od.Analysis("singletop", 1)


#
# config for 2011 Open Data @ 7 TeV
#

config_singletop_opendata_2011 = cfg = ana.add_config(campaign_opendata_2011,
    name = "singletop_opendata_2011"
)

# add datasets and processes we're interested in
# (in this example, basically everything that was defined in the campaign)
for name in ["singleTop", "WJets", "ZJets", "WWJets", "WZJets", "ZZJets"]:
    dset = cfg.add_dataset(campaign_opendata_2011.get_dataset(name))
    cfg.add_process(dset.get_process(name))

# add channels
cfg.add_channel("mu", 1,
    label       = r"$\mu$",
    label_short = "mu",
    aux         = {
        "luminosity": 5.55, # 1/fb
    },
)

# add systematic shifts
cfg.add_shift("nominal", 1)
cfg.add_shift("lumi_up", 2,   type="rate",  label="Luminosity")
cfg.add_shift("lumi_down", 3, type="rate",  label="Luminosity")
cfg.add_shift("jer_up", 4,    type="shape", label="Jet energy resolution")
cfg.add_shift("jer_down", 5,  type="shape", label="Jet energy resolution")

# variables
cfg.add_variable("jet1_pt",
    expression = "Jet1_Pt",
    binning    = (20, 0., 200.,),
    unit       = "GeV",
    x_title    = r"Leading jet $p_{T}$",
)

cfg.add_variable("weight",
    expression = "EventWeight",
    binning    = (20, 0., 1.,),
    x_title    = "Event weight",
    aux        = {"weight": False},
)
