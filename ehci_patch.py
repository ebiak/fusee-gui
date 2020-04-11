#!/usr/bin/python3
import os

"""
Cursed Code.

This code literally patches your kernel memory, proceed at your own risk.

Tested on Ubuntu 17.10 and Arch, x86_64. Should work on other distros, maybe even other architectures!

Run fusee-launcher.py with the "--override-checks" argument.

If you'd rather patch your drivers properly:
https://github.com/fail0verflow/shofel2/blob/master/linux-ehci-enable-large-ctl-xfers.patch
"""

ksyms = {
	line[2]: int(line[0], 16)
	for line in
		map(lambda l: l.strip().split(),
			open("/proc/kallsyms", "r").readlines())}

print(hex(ksyms["ehci_urb_enqueue"]))

patch_c = """
#include <linux/module.h>
#include <linux/kernel.h>
#include <asm/pgtable.h>

static u32 ORIG_MAX = 16*1024;
static u32 NEW_MAX = 0x1000000;

/* borrowed from MUSL because I'm lazy AF */
static char *fourbyte_memmem(const unsigned char *h, size_t k, const unsigned char *n)
{
	uint32_t nw = n[0]<<24 | n[1]<<16 | n[2]<<8 | n[3];
	uint32_t hw = h[0]<<24 | h[1]<<16 | h[2]<<8 | h[3];
	for (h+=3, k-=3; k; k--, hw = hw<<8 | *++h)
		if (hw == nw) return (char *)h-3;
	return 0;
}

static pte_t* (*lookup_addr)(unsigned long, unsigned int*) = (void *) PLACE2;

static void set_addr_rw(unsigned long addr) {
	unsigned int level;
	pte_t *pte = lookup_addr(addr, &level);
	set_pte_atomic(pte, pte_mkwrite(*pte));
}

int init_module(void) {
	void * ehci_urb_enqueue_start = (void *) PLACEHOLDER;
	u32 * patch_addr;

	printk(KERN_INFO "Patch module loaded\\n");
	patch_addr = (u32 *) fourbyte_memmem(ehci_urb_enqueue_start, 0x400, (void *)&ORIG_MAX);

	if (patch_addr == NULL) {
		printk(KERN_INFO "Failed to find patch site :(\\n");
		return -1;
	}

	printk(KERN_INFO "patch_addr: 0x%px\\n", patch_addr);
	set_addr_rw((unsigned long)patch_addr);
	*patch_addr = NEW_MAX;
	printk(KERN_INFO "Patching done!\\n");

	return -1;
}
""".replace("PLACEHOLDER", hex(ksyms["ehci_urb_enqueue"])).replace("PLACE2", hex(ksyms["lookup_address"]))

makefile = """
obj-m += patch.o
all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
"""

with open("patch.c", "w") as patchfile:
	patchfile.write(patch_c)

with open("Makefile", "w") as mf:
	mf.write(makefile)

os.system("make")

print("About to insert patch module, 'Operation not permitted' means it probably worked, check dmesg output.")

os.system("insmod patch.ko")