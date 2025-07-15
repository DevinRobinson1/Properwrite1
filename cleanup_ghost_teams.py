#!/usr/bin/env python3
"""
Cleanup Ghost Teams Script
Removes single-user teams that were created before the team invite fix
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from billing_models import Team, User, TeamInvite, CreditLog
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_ghost_teams():
    """
    Remove ghost teams that were created when users accepted invites
    """
    # Connect to database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment variables")
        return
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with Session() as db:
        try:
            # Find single-user teams that might be ghosts
            ghost_teams = db.query(Team).filter(
                Team.seats_max == 1,
                Team.name.like("%'s Team")
            ).all()
            
            teams_to_remove = []
            
            for team in ghost_teams:
                # Check if this team has exactly one user
                user_count = db.query(User).filter(User.team_id == team.id).count()
                
                if user_count == 1:
                    # Get the user
                    user = db.query(User).filter(User.team_id == team.id).first()
                    
                    # Check if this user has accepted any team invites
                    has_accepted_invite = db.query(TeamInvite).filter(
                        TeamInvite.email == user.email,
                        TeamInvite.status == 'accepted'
                    ).count() > 0
                    
                    if has_accepted_invite:
                        # This is likely a ghost team - user should be on another team
                        teams_to_remove.append((team, user))
                        logger.info(f"Found ghost team: {team.name} for user {user.email}")
                
                elif user_count == 0:
                    # Empty team - definitely should be removed
                    teams_to_remove.append((team, None))
                    logger.info(f"Found empty team: {team.name}")
            
            # Remove ghost teams
            for team, user in teams_to_remove:
                if user:
                    # Find the team the user should actually be on
                    accepted_invite = db.query(TeamInvite).filter(
                        TeamInvite.email == user.email,
                        TeamInvite.status == 'accepted'
                    ).first()
                    
                    if accepted_invite:
                        # Move user to the correct team
                        user.team_id = accepted_invite.team_id
                        user.role = accepted_invite.role
                        logger.info(f"Moving user {user.email} to team {accepted_invite.team_id}")
                
                # Remove the ghost team
                db.delete(team)
                logger.info(f"Removed ghost team: {team.name}")
            
            db.commit()
            logger.info(f"Cleanup complete. Removed {len(teams_to_remove)} ghost teams")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            db.rollback()
            raise

if __name__ == "__main__":
    cleanup_ghost_teams()