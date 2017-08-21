import pexpect

class BaseDevice(object):
    #TODO: Add logging
    def __init__ (self):
        self.hostname = none

    def expect(self,pattern):
        return self.child.expect(pattern)

    def write(self,command):
        self.child.sendline(command)

class BaseIOS(BaseDevice):
    #TODO: Add logging
    def __init__ (self):
        super(BaseDevice, self).__init__()
        self.logged_in, self.logged_in_msg = self.login()
    def _get_hostname(self):
        self.child.send("\n")
        self.child.expect(['#', '>'], 2)
        text = self.child.before
        self.hostname = text.replace('>', '').replace('#', '').strip()

    def cmd(self,command):
        #self.logger.info("Sending Command: %s"%(command))
        #self.logger.debug(self.child.before)
        self.write(command)

        if self.hostname is not None:
             self.child.expect(self.hostname + '(\(config(-\S+)?\))?#')
        else:
            self.child.expect('#')

        ret_text = self.child.before
        #self.logger.debug(ret_text)
        if 'hostname' in ret_text:
            self._get_hostname()

        if "Invalid input" in ret_text or "Incomplete command" in ret_text:
            #self.logger.info("Invalid Command: " + command)
            raise errors.InvalidCommand(command, self.ip)

        return ''.join(ret_text.splitlines(True)[1:])

    def login(self,**device):
    	self.child = pexpect.spawn('ssh -l '+ device['user'] + ' ' + device['ip'])
        exp_list = self.child.compile_pattern_list(['name:','[pP]assword:','#','resolve','no route','refused',pexpect.TIMEOUT,pexpect.EOF])
        while True:
            i = self.child.expect_list(exp_list)
            if i == 0:
                #self.logger.debug("Found 'name:'\n" + child.before)
                self.write(user)
                continue
            if i == 1:
                #self.logger.debug("Found '[pP]assword:'\n" + child.before)
                self.write(pw)
                continue
            if i == 2:
                #self.logger.debug("Found '#'\n" + child.before)
                self.cmd('term len 0')
                break
            if i == 3:
                return (0,'Could not resolve hostname')
            if i == 4:
                return (0,'No route to host')
            if i == 5:
                return (0,'Refused connection')
            if i == 6:
                return (0,'Timed-out')
            if i == 7:
                #logger.debug(child.before)
                return (0, 'EOF received')
        self._get_hostname()
        return (1, 'Successfully Logged in')

class BaseWLC(BaseDevice):

    def __init__ (self):
        super(BaseDevice, self).__init__()
        self.logged_in, self.logged_in_msg = self.login()

    def _get_hostname(self):
        self.child.send("\n")
        self.child.expect('>')
        text = self.child.before
        self.hostname = text.replace(' ) >', '').replace('( ', '').strip()

    def cmd(self,command):
        #self.logger.info("Sending Command: %s"%(command))
        #self.logger.debug(self.child.before)
        self.write(command)

        if self.hostname is not None:
             self.child.expect('(' + self.hostname + ') >')
        else:
            self.child.expect('>')

        ret_text = self.child.before
        #self.logger.debug(ret_text)
        if 'hostname' in ret_text:
            self._get_hostname()

        if "Incorrect usage" in ret_text:
            #self.logger.info("Invalid Command: " + command)
            raise errors.InvalidCommand(command, self.ip)

        return ''.join(ret_text.splitlines(True)[1:])
