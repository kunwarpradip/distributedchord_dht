from chord import Local, Daemon, repeat_and_sleep, inrange
from remote import Remote
from address import Address
from metrics import metrics_registry
import json
import socket
import time

# data structure that represents a distributed hash table
class DHT(object):
	def __init__(self, local_address, remote_address = None):
		self.local_ = Local(local_address, remote_address)
		def set_wrap(msg):
			return self._set(msg)
		def get_wrap(msg):
			return self._get(msg)

		self.data_ = {}
		self.shutdown_ = False

		self.local_.register_command("set", set_wrap)
		self.local_.register_command("get", get_wrap)

		self.daemons_ = {}
		self.daemons_['distribute_data'] = Daemon(self, 'distribute_data')
		self.daemons_['distribute_data'].start()

		self.local_.start()

	def shutdown(self):
		self.local_.shutdown()
		self.shutdown_ = True

	def _get(self, request):
		start = time.monotonic()
		try:
			data = json.loads(request)
			# we have the key
			result = json.dumps({'status':'ok', 'data':self.get(data['key'])})
			metrics_registry.record_latency("dht.rpc.get", (time.monotonic() - start) * 1000)
			metrics_registry.increment("dht.rpc.get.success")
			return result
		except Exception:
			# key not present
			metrics_registry.record_latency("dht.rpc.get.failed", (time.monotonic() - start) * 1000)
			metrics_registry.increment("dht.rpc.get.failure")
			return json.dumps({'status':'failed'})

	def _set(self, request):
		start = time.monotonic()
		try:
			data = json.loads(request)
			key = data['key']
			value = data['value']
			self.set(key, value)
			metrics_registry.record_latency("dht.rpc.set", (time.monotonic() - start) * 1000)
			metrics_registry.increment("dht.rpc.set.success")
			return json.dumps({'status':'ok'})
		except Exception:
			# something is not working
			metrics_registry.record_latency("dht.rpc.set.failed", (time.monotonic() - start) * 1000)
			metrics_registry.increment("dht.rpc.set.failure")
			return json.dumps({'status':'failed'})

	def get(self, key):
		try:
			# Data is local
			metrics_registry.increment("dht.get.local_hits")
			return self.data_[key]
		except Exception:
			# not in our range - need remote lookup
			metrics_registry.increment("dht.get.remote_lookups")
			suc = self.local_.find_successor(hash(key))
			if self.local_.id() == suc.id():
				# it's us but we don't have it
				metrics_registry.increment("dht.get.miss")
				return None
			try:
				response = suc.command('get %s' % json.dumps({'key':key}))
				if not response:
					raise Exception
				value = json.loads(response)
				if value['status'] != 'ok':
					raise Exception
				return value['data']
			except Exception:
				return None
	def set(self, key, value):
		# eventually it will distribute the keys
		self.data_[key] = value

	@repeat_and_sleep(5)
	def distribute_data(self):
		to_remove = []
		# to prevent from RTE in case data gets updated by other thread
		keys = list(self.data_.keys())  # Create a snapshot copy to avoid RuntimeError
		for key in keys:
			if self.local_.predecessor() and \
			   not inrange(hash(key), self.local_.predecessor().id(1), self.local_.id(1)):
				try:
					node = self.local_.find_successor(hash(key))
					node.command("set %s" % json.dumps({'key':key, 'value':self.data_[key]}))
					# Only add to removal list if migration succeeded
					to_remove.append(key)
					# print("moved %s into %s" % (key, node.id()))
					print("migrated")
				except (socket.error, json.JSONDecodeError):
					# Silently ignore errors during migration (packet loss, shutdown, etc.)
					# Key will be retried on next iteration
					pass
				except Exception:
					# Catch all other exceptions to prevent thread crashes
					pass
		# remove all the keys we do not own any more
		for key in to_remove:
			del self.data_[key]
		# Keep calling us
		return True

def create_dht(lport):
	laddress = map(lambda port: Address('127.0.0.1', port), lport)
	r = [DHT(laddress[0])]
	for address in laddress[1:]:
		r.append(DHT(address, laddress[0]))
	return r


if __name__ == "__main__":
	import sys
	if len(sys.argv) == 2:
		dht = DHT(Address("127.0.0.1", sys.argv[1]))
	else:
		dht = DHT(Address("127.0.0.1", sys.argv[1]), Address("127.0.0.1", sys.argv[2]))
	input("Press any key to shutdown")
	print("shuting down..")
	dht.shutdown()

