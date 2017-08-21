import pexpect
from niah import errors

class BaseDevice(object):
    #TODO: Add logging
    def __init__ (self,session):
        self.hostname = none
        self.child = session

    def expect(self,pattern):
        return self.child.expect(pattern)

    def write(self,command):
        self.child.sendline(command)

class BaseIOS(BaseDevice):
    #TODO: Add logging
    def __init__ (self,session):
        super(BaseDevice, self).__init__(session)

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

class BaseWLC(BaseDevice):

    def __init__ (self,session):
        super(BaseDevice, self).__init__(session)

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
