FROM aiidateam/aiida-core:latest

# Set HOME, PATH and RASPA_DIR variables:
ENV PATH="/opt/RASPA2_installed/bin/:${PATH}"
ENV RASPA2_DIR=/opt/RASPA2_installed
ENV KILL_ALL_RPOCESSES_TIMEOUT=50

# Install necessary codes to build RASPA2.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && apt-get update && apt-get install -y --no-install-recommends  \
    automake \
    libtool

# Download, compile and install RASPA into ~/code folder.
WORKDIR /opt/
RUN git clone --depth 1 --branch v2.0.41 https://github.com/iRASPA/RASPA2.git RASPA2
WORKDIR /opt/RASPA2
RUN rm -rf autom4te.cache
RUN mkdir m4
RUN aclocal
RUN autoreconf -i
RUN automake --add-missing
RUN autoconf
RUN ./configure --prefix=${RASPA2_DIR}
RUN make
RUN make install

WORKDIR /opt/

# Install coveralls.
RUN pip install coveralls

# Copy and install aiida-raspa plugin.
COPY . aiida-raspa
RUN pip install ./aiida-raspa[pre-commit,test,docs]

# Install the RASPA code to AiiDA.
COPY .docker/opt/add-codes.sh /opt/
COPY .docker/my_init.d/add-codes.sh /etc/my_init.d/50_add-codes.sh
