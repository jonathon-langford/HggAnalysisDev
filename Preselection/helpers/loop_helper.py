import json
import glob
import uproot
import pandas
import numpy
import awkward

import selections.photon_selections as photon_selections
import selections.analysis_selections as analysis_selections
import selections.lepton_selections as lepton_selections
import selections.tau_selections as tau_selections

class LoopHelper():
    """
    Class to perform all looping activities: looping through samples,
    filling histograms, making data/MC plots, yield tables,
    writing a single ntuple with all events, etc
    """

    def __init__(self, **kwargs):
        self.samples = kwargs.get("samples")
        self.selections = kwargs.get("selections")
        self.options = kwargs.get("options")
        self.systematics = kwargs.get("systematics")
        self.years = kwargs.get("years").split(",")

        self.output_tag = kwargs.get("output_tag")
        
        self.batch = kwargs.get("batch")
        self.nCores = kwargs.get("nCores")
        self.debug = kwargs.get("debug")
        self.fast = kwargs.get("fast")

        self.do_plots = kwargs.get("do_plots")
        self.do_tables = kwargs.get("do_tables")
        self.do_ntuple = kwargs.get("do_ntuple")

        if self.debug > 0:
            print("[LoopHelper] Creating LoopHelper instance with options:")
            print("\n".join(["{0}={1!r}".format(a, b) for a, b in kwargs.items()]))

        with open(self.options, "r") as f_in:
            options = json.load(f_in)
            for key, info in options.items():
                setattr(self, key, info)

        self.save_branches.append("process_id")
        self.save_branches.append("weight")

        self.branches_data = [branch for branch in self.branches if "gen" not in branch]
        self.save_branches_data = [branch for branch in self.save_branches if "gen" not in branch]
        

        if self.debug > 0:
            print("[LoopHelper] Opening options file: %s" % self.options)
            print("[LoopHelper] Options loaded as:")
            print("\n".join(["{0}={1!r}".format(a, b) for a, b in options.items()]))

        self.load_samples()

    
    def load_file(self, file, tree_name = "Events", data = False):
        with uproot.open(file) as f:
            tree = f[tree_name]
            if data:
                branches = self.branches_data
            else:
                branches = self.branches
            events = tree.arrays(branches, library = "ak", how = "zip") 
            #events = tree.arrays(branches, entry_start = 0, entry_stop = 10000, library = "ak", how = "zip") 
            # library = "ak" to load arrays as awkward arrays for best performance
            # how = "zip" allows us to access arrays as records, e.g. events.Photon
        return events

    def select_events(self, events):
        # Dipho preselection
        events = photon_selections.diphoton_preselection(events, self.debug)
        events.Photon = events.Photon[photon_selections.select_photons(events, self.debug)]

        if self.selections == "HHggTauTau_InclusivePresel":
            events = analysis_selections.ggTauTau_inclusive_preselection(events, self.debug)
            events.Electron = lepton_selections.select_electrons(events, self.debug)
            events.Muon = lepton_selections.select_muons(events, self.debug)
            events.Tau = tau_selections.select_taus(events, self.debug)
            return events 

    def trim_events(self, events, data):
        events = photon_selections.set_photons(events, self.debug)
        #events = lepton_selections.set_electrons(events, self.debug)
        #events = lepton_selections.set_muons(events, self.debug)
        if data:
            branches = self.save_branches_data
        else:
            branches = self.save_branches
        trimmed_events = events[branches]
        return trimmed_events


        # TODO: figure out how to trim object branches
        """
        events = photon_selections.set_photons(events, self.debug)

        if data:
            branches = self.save_branches_data
        else:
            branches = self.save_branches

        trimmed_events = events
        #trimmed_events = events[branches] 
        #a = events[["ggMass", "MET_pt"]]
        #b = events.Photon[["pt", "eta"]]
        #trimmed_events = awkward.zip([a,b])
        return trimmed_events
        """

    def load_samples(self):
        with open(self.samples, "r") as f_in:
            self.samples_dict = json.load(f_in)

        if self.debug > 0:
            print("[LoopHelper] Running over the following samples:")
            print("\n".join(["{0}={1!r}".format(a, b) for a, b in self.samples_dict.items()]))

    def run(self):
        events = []
        for sample, info in self.samples_dict.items():
            if self.debug > 0:
                print("[LoopHelper] Running over sample: %s" % sample)
                print("[LoopHelper] details: ", info)

            events_sample = self.loop_sample(sample, info)
            events.append(events_sample)   

        events_full = awkward.concatenate(events)
        self.write_to_df(events_full)

    def write_to_df(self, events):
        df = awkward.to_pandas(events)
        df.to_pickle("output/events_%s_%s.pkl" % (self.selections, self.output_tag))

    def loop_sample(self, sample, info):
        if sample == "Data":
            data = True
        else:
            data = False
        
        sel_evts = []
        process_id = info["process_id"]

        for year, year_info in info.items():
            if year not in self.years:
                continue

            files = []
            for path in year_info["paths"]:
                files += glob.glob(path + "/*.root")

            if len(files) == 0:
                if self.debug > 0:
                    print("[LoopHelper] Sample %s, year %s, has 0 input files, skipping." % (sample, year))
                continue
            
            counter = 0
            for file in files:
                counter += 1
                if self.fast and counter >= 2:
                    continue
                if self.debug > 0:
                    print("[LoopHelper] Loading file %s" % file)

                events = self.load_file(file, data = data)
                selected_events = self.select_events(events) #self.select_events(events)

                selected_events["process_id"] = numpy.ones(len(selected_events)) * process_id

                if data:
                    selected_events["weight"] = numpy.ones(len(selected_events))
                else:
                    selected_events["weight"] = selected_events.genWeight * year_info["metadata"]["scale1fb"]

                selected_events_trimmed = self.trim_events(selected_events, data)
                sel_evts.append(selected_events_trimmed)

        selected_events_full = awkward.concatenate(sel_evts)
        return selected_events_full
