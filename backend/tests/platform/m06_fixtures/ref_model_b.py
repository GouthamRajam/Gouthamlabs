# Hand-written test fixture (scripted model answer). Not agent output.
class RefModel:
    def reset(self):
        self.count = 0

    def step(self, txn):
        if not txn["rst_n"]:
            self.count = 0
        elif txn["load"]:
            self.count = txn["load_value"] & 0xFF
        elif txn["en"]:
            self.count = (self.count + 1) % 256 if txn["up"] else (self.count - 1) % 256
        return {"count": self.count}
