#!/usr/bin/env bash
# Should be ran from the pre-launch command in instance's settings.
# Edits by RaptaG (https://github.com/RaptaG)

# Select the mods you wish to disable:
mod0=
mod1=
mod2=
mod3=
mod4=
mod5=

# Upgrading Together Optimized
echo "Checking for Together Optimized upgrades..."
cd ..
mcver="$(jq -r '.components[]|select(.cachedName=="Minecraft")|.version' mmc-pack.json)"
if [ -d .minecraft ]; then
	cd .minecraft/
else
	cd minecraft/
fi
"$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/College-Debt-SMP/together-optimized/main/Packwiz/${mcver}/pack.toml

# Disabling the mods
echo "Disabling mods..."
cd mods
for mod in\
	$mod1.jar\
	$mod2.jar\
	$mod3.jar\
	$mod4.jar\
	$mod5.jar\
	$mod0.jar
do
	mv ${mod} .$(basename ${mod} .jar).jar.disabled
	echo "${mod} disabled successfully!"
done
