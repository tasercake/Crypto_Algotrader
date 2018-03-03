import time
import logging
import requests
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class Service(metaclass=ABCMeta):
    # TODO: add postprocessing method
    # TODO: add instance-level switch to enable postprocessing in the request() method
    def __init__(self, name: str, root: str, key_file: str=None, default_api_version=None):
        self.name = name
        self.root = root
        self.key_loaded = False
        self.api_key, self.secret_key = None, None
        self.default_api_version = default_api_version
        if key_file is not None:
            self.read_key_file(key_file)
        logger.debug("Initialized {} environment".format(name))

    # region Helper methods
    @property
    def timestamp(self) -> int:
        """
        Truncated timestamp in milliseconds

        Returns:
            int: millisecond UNIX timestamp
        """
        return int(1000 * (time.time()))

    @property
    def nonce(self):
        """
        Returns a value that is always larger than the last

        Returns:
            int: millisecond timestamp (by default)
        """
        return int(time.time() * 1000)

    def get_default_params(self, **kwargs) -> dict:
        """
        Creates a dictionary of paramters to be sent by default along with every request

        Args:
            **kwargs: Keywork arguments that may be used to determine the default parameters

        Returns:
            dict: Default parameter dictionary
        """
        return {}

    def get_final_params(self, **kwargs) -> dict:
        """
        Get the final parameters to send with the request.

        Args:
            **kwargs: Keywork arguments that may be used to determine the default parameters

        Returns:
            dict: Dictionary containing the final parameters to be sent with the request
        """
        final_params = self.get_default_params(**kwargs)
        if 'params' in kwargs:
            params = kwargs['params']
            if params is not None:
                final_params.update(params)
        return final_params

    def read_key_file(self, key_file) -> tuple:
        """
        Loads the public and private API keys from a given file into self.api_key and self.secret_key.

        Args:
            key_file: Path to file containing API key and secret.
            The two keys must be on different lines, and the file must contain exactly 2 lines.

        Returns:
            tuple: (API key, Secret key)
        """
        if key_file is not None:
            with open(key_file, 'rb') as file:
                api_key = file.readline().strip()
                secret_key = file.readline().strip()
            self.key_loaded = True
            return api_key, secret_key
        else:
            return None, None

    def _json_number_hook(self, inp):
        if isinstance(inp, list):
            for k, v in enumerate(inp):
                # check values for integers
                if isinstance(v, (list, dict)):
                    inp[k] = self._json_number_hook(v)
                else:
                    try:
                        f = float(v)
                        if f.is_integer():
                            f = int(f)
                        inp[k] = f
                    except (ValueError, TypeError):
                        pass
        elif isinstance(inp, dict):
            for k, v in inp.items():
                # check values for integers
                if isinstance(v, (list, dict)):
                    inp[k] = self._json_number_hook(v)
                else:
                    try:
                        f = float(v)
                        if f.is_integer():
                            f = int(f)
                        inp[k] = f
                    except (ValueError, TypeError):
                        pass
        return inp

    @abstractmethod
    def validate_arguments(self, method: str, *args, **kwargs) -> bool:
        """
        Validate all arguments for any given method.

        Args:
            method (str): Name of method to verify arguments for
            *args: List of positional arguments
            **kwargs: Dict of keyword arguments

        Returns:
            bool: True if arguments are valid, False otherwise
        """
        return True

    @abstractmethod
    def sign_request(self, request: requests.Request):
        """
        Sign the request with the secret key.

        Args:
            request (requests.Request):

        Returns:

        """
        pass

    @abstractmethod
    def add_api_key(self, request: requests.Request):
        """
        Adds API key to the request object.

        Args:
            request (requests.Request): Request object to add the API key to

        Returns:
            None
        """
        pass
    # endregion

    # region Request methods
    def request(self, request_type: str, endpoint: str, params=None,
                api_version=None, data=None, headers=None, sign=False) -> requests.Response:
        """
        Send a synchronous request to an API endpoint.

        Args:
            request_type (str): get | post | put | delete.
            endpoint (str): API endpoint to send the request to, for example: '24hticker'
            params (dict): Dictionary-like object containing the parameters to send with request
            api_version (str): API version to send the request to
            data (dict): Dictionary-like object containing the data to send with request
            headers (dict): Additional headers to send with the request
            sign (bool): whether or not to sign the request using the secret key

        Returns:

        """
        arguments = locals()
        if api_version is None:
            api_version = self.default_api_version
        final_params = self.__class__.get_final_params(**arguments)
        logger.debug('Querying {}'.format(self.name))
        request = requests.Request(None, self.root + "/{}/".format(api_version) + endpoint,
                                   params=final_params, data=data, headers=headers)

        # TODO: implement rate limiter

        with requests.Session() as session:
            try:
                assert request_type in ('get', 'post', 'put', 'delete')
                request.method = request_type.upper()
            except AssertionError:
                logger.critical('invalid request type {}'.format(request_type))

            if sign:
                self.sign_request(request)
            self.add_api_key(request)
            prepped = request.prepare()
            response = session.send(prepped)
        return response

    def get(self, endpoint: str, params=None, api_version=None,
            data=None, headers=None, sign=False) -> requests.Response:
        return self.request('get', endpoint, params=params, api_version=api_version,
                            data=data, headers=headers, sign=sign)

    def post(self, endpoint: str, params=None, api_version=None,
             data=None, headers=None, sign=False) -> requests.Response:
        return self.request('post', endpoint, params=params, api_version=api_version,
                            data=data, headers=headers, sign=sign)

    def put(self, endpoint: str, params=None, api_version=None,
            data=None, headers=None, sign=False) -> requests.Response:
        return self.request('put', endpoint, params=params, api_version=api_version,
                            data=data, headers=headers, sign=sign)

    def delete(self, endpoint: str, params=None, api_version=None,
               data=None, headers=None, sign=False) -> requests.Response:
        return self.request('delete', endpoint, params=params, api_version=api_version,
                            data=data, headers=headers, sign=sign)

    # endregion
    pass


if __name__ == '__main__':
    print(Ellipsis)
