# Dockerfile for creating a package from the website .jar.

FROM ubuntu:26.04 AS website-run

SHELL [ "/bin/bash", "-c" ]

ENV USER=website
RUN apt update && \
    apt upgrade -y && \
\
    # Add the Adoptium repository to the apt sources and update.
    apt update && \
    apt install -y apt-transport-https gpg wget && \
    wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | \
        gpg --dearmor | \
        tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null && \
    VERSION_CODENAME=$(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) && \
    echo "deb https://packages.adoptium.net/artifactory/deb $VERSION_CODENAME main" | \
        tee /etc/apt/sources.list.d/adoptium.list > /dev/null && \
    apt update && \
\
    # Install the JRE.
    apt install --no-install-recommends -y fakeroot temurin-25-jre && \
\
    # Clean up the apt cache.
    apt clean && \
    rm -rf /var/lib/apt/lists/* && \
\
    # Add user for running the application.
    useradd -m -s /bin/bash ${USER}

USER $USER
WORKDIR /tmp

COPY --chown=$USER target/website*.jar website.jar

CMD [ "java", "-jar", "website.jar" ]
