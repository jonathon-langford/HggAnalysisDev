import awkward
import numpy
import numba

import selections.selection_utils as utils
import selections.object_selections as object_selections
import selections.lepton_selections as lepton_selections
import selections.tau_selections as tau_selections
import selections.photon_selections as photon_selections
import selections.jet_selections as jet_selections

def ggTauTau_inclusive_preselection(events, photons, electrons, muons, taus, jets, options, debug):
    """
    Performs inclusive ggTauTau preselection, requiring >=1 (leptons + tau_h).
    Assumes diphoton preselection has already been applied.
    Also calculates relevant event-level variables.
    """
    cut_diagnostics = utils.CutDiagnostics(events = events, debug = debug, cut_set = "[analysis_selections.py : ggTauTau_inclusive_preselection]")

    # Get number of electrons, muons, taus
    selected_electrons = electrons[lepton_selections.select_electrons(events, photons, electrons, options, debug)]
    selected_muons = muons[lepton_selections.select_muons(events, photons, muons, options, debug)]
    selected_taus = taus[tau_selections.select_taus(events, photons, selected_muons, selected_electrons, taus, options, debug)]

    n_electrons = awkward.num(selected_electrons)
    n_muons = awkward.num(selected_muons)
    n_taus = awkward.num(selected_taus)

    # Require >= 1 lep/tau
    n_leptons_and_taus = n_electrons + n_muons + n_taus
    lep_tau_cut = n_leptons_and_taus >= options["n_leptons_and_taus"] 

    # Require OS leptons/taus for events with 2 leptons/taus
    sum_charge = awkward.sum(selected_electrons.charge, axis=1) + awkward.sum(selected_muons.charge, axis=1) + awkward.sum(selected_taus.charge, axis=1)
    charge_cut = sum_charge == 0
    two_leptons = n_leptons_and_taus == 2
    not_two_leptons = n_leptons_and_taus != 2
    os_cut = (two_leptons & charge_cut) | not_two_leptons # only require 2 OS leptons if there are ==2 leptons in the event

    # Select jets (don't cut on jet quantities for selection, but they will be useful for BDT training)
    selected_jets = jets[jet_selections.select_jets(events, photons, selected_electrons, selected_muons, selected_taus, jets, options, debug)]

    all_cuts = lep_tau_cut & os_cut
    cut_diagnostics.add_cuts([lep_tau_cut, os_cut, all_cuts], ["N_leptons + N_taus >= 1", "OS dileptons", "all"])

    # Keep only selected events
    selected_events = events[all_cuts]
    selected_photons = photons[all_cuts]
    selected_electrons = selected_electrons[all_cuts]
    selected_muons = selected_muons[all_cuts]
    selected_taus = selected_taus[all_cuts]
    selected_jets = selected_jets[all_cuts]

    # Calculate event-level variables
    selected_events = lepton_selections.set_electrons(selected_events, selected_electrons, debug)
    selected_events = lepton_selections.set_muons(selected_events, selected_muons, debug)
    selected_events = tau_selections.set_taus(selected_events, selected_taus, debug)
    selected_events = jet_selections.set_jets(selected_events, selected_jets, options, debug)  
    # TODO: add calculation HH->ggTauTau specific variables (e.g. H->TauTau kinematics) here

    return selected_events

def tth_leptonic_preselection(events, photons, electrons, muons, jets, options, debug):
    """
    Performs tth leptonic preselection, requiring >= 1 lepton and >= 1 jet
    Assumes diphoton preselection has already been applied.
    Also calculates relevant event-level variables.
    """

    cut_diagnostics = utils.CutDiagnostics(events = events, debug = debug, cut_set = "[analysis_selections.py : tth_leptonic_preselection]")
    
    # Get number of electrons, muons

    selected_electrons = electrons[lepton_selections.select_electrons(events, photons, electrons, options, debug)]
    selected_muons = muons[lepton_selections.select_muons(events, photons, muons, options, debug)]

    n_electrons = awkward.num(selected_electrons)
    n_muons = awkward.num(selected_muons)
    n_leptons = n_electrons + n_muons
    
    # Get number of jets
    selected_jets = jets[jet_selections.select_jets(events, photons, selected_electrons, selected_muons, None, jets, options, debug)]
    n_jets = awkward.num(selected_jets)

    lep_cut = n_leptons >= 1
    jet_cut = n_jets >= 1

    all_cuts = lep_cut & jet_cut
    cut_diagnostics.add_cuts([lep_cut, jet_cut, all_cuts], ["N_leptons >= 1", "N_jets >= 1", "all"])

    # Keep only selected events
    selected_events = events[all_cuts]
    selected_photons = photons[all_cuts]
    selected_electrons = selected_electrons[all_cuts]
    selected_muons = selected_muons[all_cuts]
    selected_jets = selected_jets[all_cuts]

    # Calculate event-level variables
    selected_events = lepton_selections.set_electrons(selected_events, selected_electrons, debug)
    selected_events = lepton_selections.set_muons(selected_events, selected_muons, debug)
    selected_events = jet_selections.set_jets(selected_events, selected_jets, options, debug)

    return selected_events
