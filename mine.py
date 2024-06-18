import os
from collections import defaultdict
from Declare4Py.ProcessModels.DeclareModel import DeclareModel
from Declare4Py.ProcessMiningTasks.Discovery.DeclareMiner import DeclareMiner
from Declare4Py.D4PyEventLog import D4PyEventLog
from argparse import ArgumentParser
from pathlib import Path
from math import ceil
import random 
import sys

template_to_ltlf = {
	'response': "G(({arg_0}) -> X(F({arg_1})))",
	'chain_response': "G(({arg_0}) -> X({arg_1}))",
    'precedence': "~({arg_1}) W {arg_0}",
	'alternate_precedence': "(~({arg_1}) W ({arg_0})) & G({arg_1} -> wX( ~({arg_1}) W {arg_0} ))",
	'chain_precedence': "G(X({arg_1}) -> {arg_0}) & ~({arg_1})",
	'succession': "G({arg_0} -> F({arg_1})) & (~({arg_1}) W {arg_0})",
	'alternate_succession': "(G({arg_0} -> X(~({arg_0}) U {arg_1})) & (~({arg_1}) W {arg_0})) & G({arg_1} -> X(~({arg_1}) W {arg_0}))",
	'chain_succession': "G({arg_0} -> X({arg_1})) & G(X({arg_1}) -> {arg_0})",
	'choice': "F({arg_0}) | F({arg_1})",
	'exclusive_choice': "F({arg_0}) | F({arg_1})) & ~(F({arg_0}) & F({arg_1}))",
	'responded_existence': "F({arg_0}) -> F({arg_1})",
	'coexistence': "(F({arg_0}) -> F({arg_1})) & (F({arg_1}) -> F({arg_0}))"
}

def get_log_activities(log):
	return set(log.get_event_attribute_values('concept:name').keys())

def declare_assumption(activities):
	implications = []
	from itertools import combinations

	# at most one
	for a1, a2 in combinations(activities, 2):
		implications.append("G({} -> ~({}))".format(a1, a2))
		implications.append("G({} -> ~({}))".format(a2, a1))

	# at least one
	big_or = "|".join(["({})".format(x) for x in activities])
	return "&".join(implications) + "&" + "G(" + big_or + ")"

def minlength(n):
	return "(" + "X " * n + "True" + ")"

def activities_sequence():
	x = 0
	while True:
		yield 'a{}'.format(x)
		x += 1

def remap_activities(activities):
	activity_identifiers = activities_sequence()
	activity_map = dict()
	for a in activities:
		activity_map[a] = next(activity_identifiers)
	return activity_map

def parse_args():
	def parse_int_list(x):
		return [int(z) for z in x.split(',')]

	def parse_float_list(x):
		return [float(z) for z in x.split(',')]

	p = ArgumentParser()	
	p.add_argument('log_folder', type=Path, help="Path to folder containing XES files.")
	p.add_argument('output_folder', type=Path, help="Path to folder that stores output formulae.")
	p.add_argument('-l', type=parse_int_list, default="16,32,64,128,256,512", help="Comma-separated minimum lengths for models.")
	p.add_argument('-p', type=parse_float_list, default="0.20,0.40,0.60,0.80", help="Fractions of constraints to sample.")
	p.add_argument('-k', type=int, default=5, help="Number of samples for each (l,p) configuration.")

	return p.parse_args()

def mine_constraints_from_log(log):
	discovery = DeclareMiner(log=log, consider_vacuity=False, min_support=0.55, itemsets_support=0.5, max_declare_cardinality=1)
	model = discovery.run()

	return [c for c in model.constraints if c['template'].name.lower() in template_to_ltlf and not c['template'].name.startswith('NOT')]

def constraint_to_ltlf(constraint, activity_map):
	formula = template_to_ltlf[constraint['template'].name.lower()]
	arg0, arg1 = [activity_map[a] for a in constraint['activities']]
	r = formula.format(arg_0=arg0, arg_1=arg1)
	return r

if __name__ == '__main__':
	args = parse_args()
	log_folder = args.log_folder
	output_folder = args.output_folder
	lenghts = args.l
	constraints_fractions = args.p
	repeats = args.k

	available_logs = list(log_folder.glob("*.xes"))
	num_logs = len(available_logs)
	for log_n, log in enumerate(available_logs, start=1):
		print(" {}/{} ".format(log_n, num_logs).center(80, "%"))
		print("Processing:", log)
		# Reading event log
		event_log = D4PyEventLog()
		event_log.parse_xes_log(log.as_posix())

		# Activities
		activities = get_log_activities(event_log)
		activity_map = remap_activities(activities)
		activities = set(activity_map.values())

		# Mine constraints
		constraints = mine_constraints_from_log(event_log)
		print("Discovery complete:", log)
		print("Available constraints:", len(constraints))

		for p in constraints_fractions:
			for k in range(repeats):
				for l in lenghts:
					con_subset = random.sample(constraints, ceil(p * len(constraints)))
					mask = output_folder / f"{log.stem}_{len(con_subset)}_{l}_{k}.ltlf"
					conjuncts = [constraint_to_ltlf(c, activity_map) for c in con_subset if c['template'].name.lower() in template_to_ltlf]

					conjuncts.append(declare_assumption(activities))
					conjuncts.append(minlength(l))

					with mask.open('w') as f:
						f.write(" & ".join("({})".format(c) for c in conjuncts))
						f.flush()
